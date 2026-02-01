# # core/rag_retriever.py
# from __future__ import annotations

# import json
# from dataclasses import dataclass
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# import numpy as np
# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer

# from sentence_transformers import SentenceTransformer

# BASE_DIR = Path(__file__).resolve().parent.parent


# @dataclass
# class RagConfig:
#     module_code: str
#     top_k: int = 4

#     @property
#     def embeddings_path(self) -> Path:
#         return BASE_DIR / "embeddings" / f"{self.module_code}_embeddings.npy"

#     @property
#     def texts_path(self) -> Path:
#         return BASE_DIR / "embeddings" / f"{self.module_code}_texts.json"


# class RagRetriever:
#     def __init__(self, config: RagConfig, model_name: str = "all-MiniLM-L6-v2"):
#         self.config = config

#         if not self.config.embeddings_path.exists():
#             raise FileNotFoundError(f"Embeddings introuvables: {self.config.embeddings_path}")

#         if not self.config.texts_path.exists():
#             raise FileNotFoundError(f"Texts introuvables: {self.config.texts_path}")

#         self.embeddings = np.load(self.config.embeddings_path).astype("float32")  # (N, d)

#         with open(self.config.texts_path, "r", encoding="utf-8") as f:
#             self.docs: List[Dict[str, Any]] = json.load(f)  # [{"text":..., "metadata":...}, ...]

#         if len(self.docs) != self.embeddings.shape[0]:
#             raise ValueError(
#                 f"Incohérence: docs={len(self.docs)} vs embeddings={self.embeddings.shape[0]}"
#             )

#         # Normaliser les embeddings docs => cosinus = dot
#         norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
#         self.embeddings = self.embeddings / norms

#         # Modèle pour encoder la requête
#         self.model = SentenceTransformer(model_name)

#     def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
#         query = (query or "").strip()
#         if not query:
#             return []

#         k = k or self.config.top_k

#         q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].astype("float32")
#         sims = self.embeddings @ q  # (N,)
#         top_idx = np.argsort(-sims)[:k]

#         results: List[Dict[str, Any]] = []
#         for i in top_idx:
#             d = self.docs[int(i)]
#             results.append({
#                 "text": d.get("text", ""),
#                 "metadata": d.get("metadata", {}),
#                 "score": float(sims[int(i)]),
#             })
#         return results
    
#     def open_exos_collection(module_code: str = "420-111"):
#         name = f"{module_code}_exercices"
#         persist_dir = Path("embeddings") / "chroma" / name

#         client = chromadb.PersistentClient(
#             path=str(persist_dir),
#             settings=Settings(anonymized_telemetry=False),
#         )
#         col = client.get_collection(name)
#         embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
#         return col, embedder


# core/rag_retriever.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import time
import streamlit as st


import numpy as np

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ cache global du modèle (évite de le recharger à chaque rerun)
_EMBEDDER: Optional[SentenceTransformer] = None


def get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer(model_name)
    return _EMBEDDER


@dataclass
class RagConfig:
    module_code: str
    top_k: int = 4

    # 🔹 legacy files (npy/json)
    @property
    def embeddings_path(self) -> Path:
        return BASE_DIR / "embeddings" / f"{self.module_code}_embeddings.npy"

    @property
    def texts_path(self) -> Path:
        return BASE_DIR / "embeddings" / f"{self.module_code}_texts.json"

    # 🔹 chroma (Option B)
    @property
    def chroma_dir(self) -> Path:
        # ex: embeddings/chroma/420-111_exercices/
        return BASE_DIR / "embeddings" / "chroma" / f"{self.module_code}_exercices"

    @property
    def chroma_collection(self) -> str:
        return f"{self.module_code}_exercices"


class RagRetriever:
    """
    Retriever hybride:
    - priorité à Chroma (embeddings/chroma/{module}_exercices) si disponible
    - sinon fallback sur embeddings .npy + texts .json (legacy)
    """

    def __init__(self, config: RagConfig, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.config = config
        self.model_name = model_name

        # ✅ si Chroma existe, on utilise Chroma
        self.use_chroma = self.config.chroma_dir.exists()

        # ---- Mode Chroma ----
        self._chroma_client = None
        self._chroma_col = None

        # ---- Mode legacy ----
        self.embeddings: Optional[np.ndarray] = None
        self.docs: List[Dict[str, Any]] = []

        if self.use_chroma:
            self._init_chroma()
        else:
            self._init_legacy()

    # -------------------------
    # Chroma
    # -------------------------
    def _init_chroma(self) -> None:
        # ouvrir la collection persistée
        self._chroma_client = chromadb.PersistentClient(
            path=str(self.config.chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._chroma_col = self._chroma_client.get_collection(self.config.chroma_collection)

        # embedder pour la requête
        self.model = get_embedder(self.model_name)

    # -------------------------
    # Legacy npy/json
    # -------------------------
    def _init_legacy(self) -> None:
        if not self.config.embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings introuvables: {self.config.embeddings_path}")

        if not self.config.texts_path.exists():
            raise FileNotFoundError(f"Texts introuvables: {self.config.texts_path}")

        self.embeddings = np.load(self.config.embeddings_path).astype("float32")  # (N, d)

        with open(self.config.texts_path, "r", encoding="utf-8") as f:
            self.docs = json.load(f)  # [{"text":..., "metadata":...}, ...]

        if len(self.docs) != self.embeddings.shape[0]:
            raise ValueError(f"Incohérence: docs={len(self.docs)} vs embeddings={self.embeddings.shape[0]}")

        # normaliser embeddings docs => cosinus = dot
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
        self.embeddings = self.embeddings / norms

        # embedder requête
        self.model = get_embedder(self.model_name)

    # -------------------------
    # Public API
    # -------------------------
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []

        k = int(k or self.config.top_k)

        t0 = time.perf_counter()

        if self.use_chroma:
            results = self._retrieve_chroma(query, k)
        else:
            results = self._retrieve_legacy(query, k)

        retrieval_ms = (time.perf_counter() - t0) * 1000

        # 🔎 debug perf (non bloquant)
        st.session_state.setdefault("last_timing", {})
        st.session_state["last_timing"]["retrieval_ms"] = round(retrieval_ms, 1)
        st.session_state["last_timing"]["k"] = k
        st.session_state["last_timing"]["retriever"] = "chroma" if self.use_chroma else "legacy"

        return results


    # -------------------------
    # Retrieval implementations
    # -------------------------
    def _retrieve_chroma(self, query: str, k: int) -> List[Dict[str, Any]]:
        assert self._chroma_col is not None

        q_emb = self.model.encode([query]).tolist()[0]
        res = self._chroma_col.query(query_embeddings=[q_emb], n_results=k)

        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]  # distance (plus petit = meilleur)

        out: List[Dict[str, Any]] = []
        for i in range(min(len(docs), len(metas))):
            out.append({
                "text": docs[i] or "",
                "metadata": metas[i] or {},
                "score": float(-dists[i]) if i < len(dists) else 0.0,  # score approx (optionnel)
            })
        return out

    def _retrieve_legacy(self, query: str, k: int) -> List[Dict[str, Any]]:
        assert self.embeddings is not None

        q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].astype("float32")
        sims = self.embeddings @ q
        top_idx = np.argsort(-sims)[:k]

        results: List[Dict[str, Any]] = []
        for i in top_idx:
            d = self.docs[int(i)]
            results.append({
                "text": d.get("text", ""),
                "metadata": d.get("metadata", {}),
                "score": float(sims[int(i)]),
            })
        return results
