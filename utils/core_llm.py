# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Thin wrapper over Ollama HTTP API for local LLM inference."""

import json
import logging
import re

import httpx

logger = logging.getLogger(__name__)

# Regex to strip Qwen3 <think>...</think> blocks from responses
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# Regex to strip lone Unicode surrogates (U+D800..U+DFFF) from LLM JSON output.
# LLMs produce these when backslash-paths (e.g. MHG\iuhpsvc) get misinterpreted
# as \uXXXX escape sequences. Python json.loads accepts lone surrogates but
# DuckDB rejects them on INSERT.
_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


class LocalLLM:
    """Local LLM client using Ollama's REST API.

    Thread-safe: uses httpx.Client with persistent connections,
    suitable for concurrent use via ThreadPoolExecutor.
    """

    def __init__(self, model="qwen3:0.6b-q4_K_S", base_url="http://localhost:11434", num_thread=0, llm_options=None):
        self.model = model
        self.base_url = base_url
        self.num_thread = num_thread
        self._llm_options = llm_options or {}
        self._client = httpx.Client(base_url=base_url, timeout=httpx.Timeout(300.0, connect=10.0))
        self.last_meta = {}  # Ollama response metadata from last call

    def _build_options(self, mode="json"):
        """Build options dict from defaults + configured overrides."""
        if mode == "json":
            defaults = {"num_ctx": 1024, "num_predict": 300, "temperature": 0.3}
        else:
            defaults = {"num_ctx": 2048, "num_predict": 500, "temperature": 0.1}
        opts = {**defaults, **self._llm_options}
        if self.num_thread > 0:
            opts["num_thread"] = self.num_thread
        return opts

    @staticmethod
    def _strip_thinking(text):
        """Remove <think>...</think> blocks from Qwen3 responses."""
        if "<think>" in text:
            return _THINK_RE.sub("", text).strip()
        return text

    @staticmethod
    def _sanitize_surrogates(obj):
        """Remove lone Unicode surrogates from all strings in a parsed JSON structure."""
        if isinstance(obj, str):
            return _SURROGATE_RE.sub("", obj)
        if isinstance(obj, dict):
            return {LocalLLM._sanitize_surrogates(k): LocalLLM._sanitize_surrogates(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [LocalLLM._sanitize_surrogates(item) for item in obj]
        return obj

    def generate_json(self, prompt, system_prompt="", timeout=120, clear_context=True):
        """POST /api/generate with format='json'. Returns parsed dict or {"error": ...}.

        Args:
            clear_context: If True (default), explicitly clears KV cache between calls
                          to ensure no context pollution between emails.
        """
        try:
            options = self._build_options("json")
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": options,
            }
            if clear_context:
                payload["context"] = []  # Explicit empty context = fresh start
            if system_prompt:
                payload["system"] = system_prompt

            response = self._client.post("/api/generate", json=payload, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            self.last_meta = {
                "total_duration_ms": data.get("total_duration", 0) / 1e6,
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "prompt_eval_ms": data.get("prompt_eval_duration", 0) / 1e6,
                "eval_count": data.get("eval_count", 0),
                "eval_ms": data.get("eval_duration", 0) / 1e6,
            }
            raw = self._strip_thinking(data.get("response", "").strip())

            if not raw:
                return {"error": "Empty response from model", "raw": ""}

            try:
                parsed = json.loads(raw)
                return self._sanitize_surrogates(parsed)
            except json.JSONDecodeError as e:
                # Return raw response so caller can attempt repair
                return {"error": f"JSON parse: {e}", "raw": raw}
        except httpx.TimeoutException:
            self.last_meta = {}
            return {"error": "timeout"}
        except httpx.HTTPStatusError as e:
            self.last_meta = {}
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            self.last_meta = {}
            return {"error": str(e)}

    def generate_text(self, prompt, system_prompt="", timeout=120, clear_context=True):
        """POST /api/generate without JSON constraint. Returns plain text string.

        Args:
            clear_context: If True (default), explicitly clears KV cache between calls.
        """
        try:
            options = self._build_options("text")
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": options,
            }
            if clear_context:
                payload["context"] = []  # Explicit empty context = fresh start
            if system_prompt:
                payload["system"] = system_prompt

            response = self._client.post("/api/generate", json=payload, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            self.last_meta = {
                "total_duration_ms": data.get("total_duration", 0) / 1e6,
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "prompt_eval_ms": data.get("prompt_eval_duration", 0) / 1e6,
                "eval_count": data.get("eval_count", 0),
                "eval_ms": data.get("eval_duration", 0) / 1e6,
            }
            return self._strip_thinking(data.get("response", "").strip())

        except httpx.TimeoutException:
            self.last_meta = {}
            return "[error: timeout]"
        except httpx.HTTPStatusError as e:
            self.last_meta = {}
            return f"[error: HTTP {e.response.status_code}]"
        except Exception as e:
            self.last_meta = {}
            return f"[error: {e}]"

    def is_available(self):
        """GET /api/tags, check if the configured model exists."""
        try:
            response = self._client.get("/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(self.model.split(":")[0]) for m in models)
        except Exception:
            return False

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()
