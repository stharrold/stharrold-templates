import logging
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
import requests
from tqdm import tqdm

# Model Configuration
MODEL_URL = "https://huggingface.co/optimum/all-MiniLM-L6-v2/resolve/main/model.onnx"
TOKENIZER_JSON = "https://huggingface.co/optimum/all-MiniLM-L6-v2/resolve/main/tokenizer.json"
MODEL_DIR = Path("utils/models")
MODEL_PATH = MODEL_DIR / "model.onnx"

# Module-level singleton
_embedder_instance = None


def get_embedder():
    """Get or create the singleton CoreEmbedder instance."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = CoreEmbedder()
    return _embedder_instance


class CoreEmbedder:
    def __init__(self):
        self._download_model_if_needed()
        self.session = ort.InferenceSession(str(MODEL_PATH))
        # Simple tokenizer (placeholder - for production we'd use tokenizers lib or HF tokenizer)
        # For this prototype, we'll assume a simple whitespace/subword logic or require `tokenizers`
        # To avoid heavy dependencies like transformers, we'll use `tokenizers` if available,
        # or download a specific ONNX tokenizer.
        # Plan B: Use the `tokenizers` library which is lightweight.
        try:
            from tokenizers import Tokenizer

            self.tokenizer = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
        except Exception as e:
            logging.error(f"Tokenizer error: {e}. Please ensure 'tokenizers' is installed or json is present.")
            raise

    def _download_model_if_needed(self):
        if not MODEL_DIR.exists():
            MODEL_DIR.mkdir(parents=True)

        if not MODEL_PATH.exists():
            logging.info(f"Downloading ONNX model to {MODEL_PATH}...")
            self._download_file(MODEL_URL, MODEL_PATH)

        tokenizer_path = MODEL_DIR / "tokenizer.json"
        if not tokenizer_path.exists():
            logging.info("Downloading tokenizer...")
            self._download_file(TOKENIZER_JSON, tokenizer_path)

    def _download_file(self, url, dest):
        proxies = {}
        https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if https_proxy:
            proxies["https"] = https_proxy
        response = requests.get(url, stream=True, proxies=proxies if proxies else None)
        total_size = int(response.headers.get("content-length", 0))
        with (
            open(dest, "wb") as file,
            tqdm(
                desc=dest.name,
                total=total_size,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar,
        ):
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

    def embed(self, text: str) -> np.ndarray:
        """Generate float32 embedding."""
        if not text:
            return np.zeros(384, dtype=np.float32)

        # Tokenize
        encoded = self.tokenizer.encode(text)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoded.type_ids], dtype=np.int64)

        # ONNX Inference
        inputs = {"input_ids": input_ids, "attention_mask": attention_mask, "token_type_ids": token_type_ids}
        outputs = self.session.run(None, inputs)

        # Mean Pooling (simplified for this model architecture)
        # Last_hidden_state is outputs[0]
        embeddings = outputs[0]
        mask = attention_mask[:, :, None]

        sum_embeddings = np.sum(embeddings * mask, axis=1)
        sum_mask = np.sum(mask, axis=1)
        sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)
        mean_pooled = sum_embeddings / sum_mask

        # Normalize
        norm = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
        normalized = mean_pooled / norm

        return normalized[0]

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> list[np.ndarray]:
        """Generate float32 embeddings for a list of texts in batches.

        Empty/None texts return zero vectors. Uses parallel tokenization
        and batched ONNX inference for throughput.
        """
        if not texts:
            return []

        zero = np.zeros(384, dtype=np.float32)
        results = [None] * len(texts)

        # Separate empty from non-empty, track original indices
        non_empty = [(i, t) for i, t in enumerate(texts) if t]
        for i, t in enumerate(texts):
            if not t:
                results[i] = zero.copy()

        if not non_empty:
            return results

        # Parallel tokenization
        indices, valid_texts = zip(*non_empty, strict=True)
        encoded_batch = self.tokenizer.encode_batch(list(valid_texts))

        # Process in chunks of batch_size
        for chunk_start in range(0, len(encoded_batch), batch_size):
            chunk_end = min(chunk_start + batch_size, len(encoded_batch))
            chunk = encoded_batch[chunk_start:chunk_end]
            chunk_indices = indices[chunk_start:chunk_end]

            # Pad to max length in this chunk
            max_len = max(len(enc.ids) for enc in chunk)
            n = len(chunk)

            input_ids = np.zeros((n, max_len), dtype=np.int64)
            attention_mask = np.zeros((n, max_len), dtype=np.int64)
            token_type_ids = np.zeros((n, max_len), dtype=np.int64)

            for j, enc in enumerate(chunk):
                seq_len = len(enc.ids)
                input_ids[j, :seq_len] = enc.ids
                attention_mask[j, :seq_len] = enc.attention_mask
                token_type_ids[j, :seq_len] = enc.type_ids

            # Single ONNX call for the chunk
            outputs = self.session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )

            # Mean pooling
            embeddings = outputs[0]  # (n, max_len, 384)
            mask = attention_mask[:, :, None]  # (n, max_len, 1)
            sum_embeddings = np.sum(embeddings * mask, axis=1)  # (n, 384)
            sum_mask = np.clip(np.sum(mask, axis=1), a_min=1e-9, a_max=None)
            mean_pooled = sum_embeddings / sum_mask

            # L2 normalize
            norms = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
            norms = np.clip(norms, a_min=1e-9, a_max=None)
            normalized = mean_pooled / norms

            for j, idx in enumerate(chunk_indices):
                results[idx] = normalized[j]

        return results

    def quantize_1bit(self, float_vec: np.ndarray) -> str:
        """Convert float vector to bit string."""
        # Threshold at 0.0
        bits = (float_vec > 0).astype(int)
        # Convert to string '10101...' for DuckDB BIT type
        return "".join(map(str, bits))

    def quantize_1bit_batch(self, vecs: list[np.ndarray]) -> list[str]:
        """Convert a list of float vectors to bit strings."""
        return [self.quantize_1bit(v) for v in vecs]

    def quantize_ubigint(self, float_vec: np.ndarray) -> tuple[list[int], int]:
        """Convert float vector to 6 UBIGINT values + popcount.

        Returns ([u0..u5], popcount) where each u_i is a 64-bit unsigned integer
        representing bits [i*64..(i+1)*64) of the binary quantization.
        """
        bits = (float_vec > 0).astype(np.uint8)
        ubigints = []
        for i in range(6):
            chunk = bits[i * 64 : (i + 1) * 64]
            val = int.from_bytes(np.packbits(chunk).tobytes(), "big")
            ubigints.append(val)
        popcount = int(bits.sum())
        return ubigints, popcount

    def quantize_ubigint_batch(self, vecs: list[np.ndarray]) -> list[tuple[list[int], int]]:
        """Convert a list of float vectors to UBIGINT representations."""
        return [self.quantize_ubigint(v) for v in vecs]


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    embedder = CoreEmbedder()
    vec = embedder.embed("Hello DuckDB")
    bits = embedder.quantize_1bit(vec)
    print(f"Vector dim: {len(vec)}")
    print(f"Bit string len: {len(bits)}")
    print(f"Bit string preview: {bits[:10]}...")
