# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Local embedding service using ONNX Runtime and Hugging Face Tokenizers.

Model: all-MiniLM-L6-v2 (384 dimensions)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MODEL_DIR = Path("models")


class EmbeddingService:
    """Generates semantic embeddings using a local ONNX model."""

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or MODEL_DIR
        self.model_path = self.model_dir / "model.onnx"
        self.tokenizer_path = self.model_dir / "tokenizer.json"
        self._session = None
        self._tokenizer = None

    @property
    def session(self):
        if self._session is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"ONNX model not found at {self.model_path}. "
                    f"Download all-MiniLM-L6-v2 ONNX model first."
                )
            self._session = ort.InferenceSession(
                str(self.model_path),
                providers=["CPUExecutionProvider"],
            )
        return self._session

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            if not self.tokenizer_path.exists():
                raise FileNotFoundError(
                    f"Tokenizer not found at {self.tokenizer_path}."
                )
            self._tokenizer = Tokenizer.from_file(
                str(self.tokenizer_path)
            )
            self._tokenizer.enable_padding(
                pad_id=0, pad_token="[PAD]", length=128
            )
            self._tokenizer.enable_truncation(max_length=128)
        return self._tokenizer

    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for a list of texts.

        Returns:
            numpy array of shape [n_texts, 384].
        """
        if not texts:
            return np.array([])

        encoded = self.tokenizer.encode_batch(texts)
        input_ids = np.array(
            [e.ids for e in encoded], dtype=np.int64
        )
        attention_mask = np.array(
            [e.attention_mask for e in encoded], dtype=np.int64
        )
        token_type_ids = np.array(
            [e.type_ids for e in encoded], dtype=np.int64
        )

        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        }

        output_names = [o.name for o in self.session.get_outputs()]
        outputs = self.session.run(output_names, inputs)

        last_hidden_state = outputs[0]

        # Mean pooling (exclude padding)
        mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
        sum_embeddings = np.sum(
            last_hidden_state * mask_expanded, axis=1
        )
        sum_mask = np.clip(
            mask_expanded.sum(axis=1), a_min=1e-9, a_max=None
        )
        embeddings = sum_embeddings / sum_mask

        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / np.clip(
            norms, a_min=1e-9, a_max=None
        )

        return embeddings

    @staticmethod
    def binarize_single(vector) -> str:
        """Binarize a single vector to a bitstring."""
        return "".join("1" if v > 0 else "0" for v in vector)

    def binarize(self, embeddings: np.ndarray) -> list[str]:
        """Convert float embeddings to compact bitstrings."""
        if embeddings.size == 0:
            return []
        binary = embeddings > 0
        return [
            "".join("1" if b else "0" for b in row) for row in binary
        ]

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query string."""
        return self.embed([text])[0]

    @staticmethod
    def quantize_ubigint(float_vec) -> tuple[list[int], int]:
        """Convert float vector to 6 UBIGINT values + popcount.

        Each UBIGINT holds 64 bits of the binary quantization.
        Returns ([u0..u5], popcount) for SIMD-friendly Hamming distance.
        """
        bits = (np.asarray(float_vec) > 0).astype(np.uint8)
        ubigints = []
        for i in range(6):
            chunk = bits[i * 64 : (i + 1) * 64]
            val = int.from_bytes(np.packbits(chunk).tobytes(), "big")
            ubigints.append(val)
        popcount = int(bits.sum())
        return ubigints, popcount

    def create_value_profile(self, values: list[str]) -> np.ndarray:
        """Create a semantic vector representing a list of values (centroid).
        """
        clean = [
            str(v).strip()
            for v in values
            if v is not None and str(v).strip()
        ]
        if not clean:
            return np.zeros(384, dtype=np.float32)
        embeddings = self.embed(clean)
        centroid = np.mean(embeddings, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 1e-9:
            centroid = centroid / norm
        return centroid
