"""
Embeddings Abstraction Module
Supports SentenceTransformers, Google Gemini Embeddings, OpenAI Embeddings,
and a deterministic Local Clinical Dense Vectorizer (zero-dependency).

Performance improvements:
- Gemini embeddings now use a single batch HTTP call instead of one request per text,
  reducing N*RTT to 1*RTT for document embedding.
- _local_dense_embed results are cached via cache_with_ttl to avoid recomputing
  the same clinical text twice in the same session.
- cosine_similarity uses numpy when available for vectorised computation.
"""

import os
import math
import json
import re
from typing import List, Optional

from utils_performance import cache_with_ttl

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


class EmbeddingsEngine:
    """Provides high-performance vector embeddings for clinical protocol text and patient profiles."""

    def __init__(
        self,
        provider: str = "auto",
        api_key: Optional[str] = None,
        dimension: int = 384
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.dimension = dimension
        self._st_model = None

        if self.provider == "auto":
            if os.getenv("GEMINI_API_KEY") or (self.api_key and "AIza" in (self.api_key or "")):
                self.provider = "gemini"
            elif os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
            else:
                try:
                    import sentence_transformers  # noqa: F401
                    self.provider = "sentence-transformers"
                except ImportError:
                    self.provider = "local-dense"

        if not self.api_key:
            if self.provider == "gemini":
                self.api_key = os.getenv("GEMINI_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")

        # Lazy-load SentenceTransformer only when selected
        if self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"[Embeddings Warning] Could not load SentenceTransformer: {e}. Falling back to local-dense.")
                self.provider = "local-dense"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding vector for a single string."""
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embedding vectors for a list of strings.
        All providers are called in batch where possible.
        """
        if not texts:
            return []

        # 1. SentenceTransformers — naturally batched
        if self.provider == "sentence-transformers" and self._st_model is not None:
            try:
                embeddings = self._st_model.encode(
                    texts, convert_to_numpy=False, show_progress_bar=False, batch_size=32
                )
                return [list(e) for e in embeddings]
            except Exception as e:
                print(f"[Embeddings Warning] ST error: {e}. Falling back to local-dense.")

        # 2. Google Gemini — batch via batchEmbedContents API
        if self.provider == "gemini" and self.api_key:
            result = self._gemini_batch_embed(texts)
            if result:
                return result

        # 3. OpenAI — already batched (sends all texts in one request)
        if self.provider == "openai" and self.api_key:
            result = self._openai_batch_embed(texts)
            if result:
                return result

        # 4. Deterministic Local Clinical Dense Vectorizer
        return [self._cached_local_dense_embed(t) for t in texts]

    # ------------------------------------------------------------------
    # Provider-specific batch helpers
    # ------------------------------------------------------------------

    def _gemini_batch_embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Calls Gemini batchEmbedContents — single HTTP request for up to 100 texts.
        Falls back to per-text requests if batch endpoint errors, then to local-dense.
        """
        import urllib.request

        # Try batch endpoint first
        batch_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"text-embedding-004:batchEmbedContents?key={self.api_key}"
        )
        try:
            requests_payload = [
                {"model": "models/text-embedding-004", "content": {"parts": [{"text": t[:2000]}]}}
                for t in texts
            ]
            req_data = json.dumps({"requests": requests_payload}).encode("utf-8")
            req = urllib.request.Request(
                batch_url, data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeddings_list = data.get("embeddings", [])
                if len(embeddings_list) == len(texts):
                    return [item.get("values", []) for item in embeddings_list]
        except Exception as e:
            print(f"[Embeddings Warning] Gemini batch embed error: {e}. Falling back to per-text.")

        # Fall back: individual requests (original behaviour)
        try:
            vectors = []
            single_url_tmpl = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-embedding-2-preview:embedContent?key={key}"
            )
            url = single_url_tmpl.format(key=self.api_key)
            for text in texts:
                req_data = json.dumps(
                    {"content": {"parts": [{"text": text[:2000]}]}}
                ).encode("utf-8")
                req = urllib.request.Request(
                    url, data=req_data,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    values = resp_data.get("embedding", {}).get("values", [])
                    vectors.append(values if values else self._cached_local_dense_embed(text))
            if len(vectors) == len(texts):
                return vectors
        except Exception as e:
            print(f"[Embeddings Warning] Gemini per-text embed error: {e}")

        return None

    def _openai_batch_embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Calls OpenAI embeddings API — sends all texts in a single request."""
        import urllib.request

        try:
            url = "https://api.openai.com/v1/embeddings"
            req_data = json.dumps({
                "model": "text-embedding-3-small",
                "input": [t[:8000] for t in texts],
            }).encode("utf-8")
            req = urllib.request.Request(
                url, data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                }
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            print(f"[Embeddings Warning] OpenAI embedding error: {e}")
            return None

    # ------------------------------------------------------------------
    # Local dense vectorizer (cached)
    # ------------------------------------------------------------------

    @cache_with_ttl(ttl_seconds=3600)
    def _cached_local_dense_embed(self, text: str) -> List[float]:
        """
        Cached wrapper around _local_dense_embed.
        Avoids recomputing the same text in the same session.
        """
        return self._local_dense_embed(text)

    def _local_dense_embed(self, text: str) -> List[float]:
        """
        High-fidelity semantic embedding fallback using clinical concept clusters,
        subword n-gram hashing, and cosine normalisation.
        """
        import hashlib

        dim = self.dimension
        vec = [0.0] * dim
        clean_text = text.lower()

        concept_clusters = [
            (["nsclc", "lung", "adenocarcinoma", "egfr", "osimertinib", "tyrosine", "kinase", "exon", "19", "l858r", "t790m", "gefitinib", "erlotinib"], 0, 30),
            (["pd-l1", "pdl1", "pembrolizumab", "nivolumab", "checkpoint", "immunotherapy", "tps", "atezolizumab", "ctla-4"], 30, 60),
            (["her2", "erbb2", "trastuzumab", "deruxtecan", "adc", "breast", "carcinoma", "muga", "lvef", "cardiac"], 60, 90),
            (["metastatic", "stage iv", "unresectable", "progression", "relapsed", "refractory", "advanced", "recurrent"], 90, 120),
            (["oncology", "cancer", "tumor", "ecog", "karnofsky", "creatinine", "anc", "platelets", "bilirubin", "ast", "alt"], 120, 150),
            (["brain metastases", "cns", "pneumonitis", "ild", "autoimmune", "interstitial", "heart failure", "nyha"], 150, 180),
            (["diabetes", "glucose", "insulin", "metformin", "hba1c", "pancreatic", "glycemic"], 180, 210),
        ]

        for keywords, start_idx, end_idx in concept_clusters:
            cluster_hit = sum(1 for kw in keywords if kw in clean_text)
            if cluster_hit > 0:
                weight = float(cluster_hit * 3.5)
                span = end_idx - start_idx
                for idx in range(start_idx, end_idx):
                    vec[idx] += weight / (1.0 + (idx % span))

        words = re.findall(r"\b[a-z0-9\-\+]{2,}\b", clean_text)
        for w in words:
            h_int = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            vec[h_int % dim] += 1.5
            if len(w) >= 3:
                for j in range(len(w) - 2):
                    ngram = w[j : j + 3]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    vec[h_ng % dim] += 0.4

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        else:
            vec = [1.0 / math.sqrt(dim)] * dim

        return vec

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity.  Uses numpy when available."""
        if _NUMPY_AVAILABLE:
            a = np.array(vec_a, dtype=np.float64)
            b = np.array(vec_b, dtype=np.float64)
            norm_a = float(np.linalg.norm(a))
            norm_b = float(np.linalg.norm(b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(max(0.0, min(1.0, np.dot(a, b) / (norm_a * norm_b))))

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(1.0, float(dot / (norm_a * norm_b))))
