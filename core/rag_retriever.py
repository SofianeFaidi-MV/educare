# # core/rag_retriever.py
# from __future__ import annotations

# import json
# from dataclasses import dataclass
# from pathlib import Path
# from typing import Any, Dict, List, Optional
# import time
# import streamlit as st


# import numpy as np

# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer

# BASE_DIR = Path(__file__).resolve().parent.parent

# # ✅ cache global du modèle (évite de le recharger à chaque rerun)
# _EMBEDDER: Optional[SentenceTransformer] = None


# def get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
#     global _EMBEDDER
#     if _EMBEDDER is None:
#         _EMBEDDER = SentenceTransformer(model_name)
#     return _EMBEDDER


# @dataclass
# class RagConfig:
#     module_code: str
#     top_k: int = 4

#     # 🔹 legacy files (npy/json)
#     @property
#     def embeddings_path(self) -> Path:
#         return BASE_DIR / "embeddings" / f"{self.module_code}_embeddings.npy"

#     @property
#     def texts_path(self) -> Path:
#         return BASE_DIR / "embeddings" / f"{self.module_code}_texts.json"

#     # 🔹 chroma (Option B)
#     @property
#     def chroma_dir(self) -> Path:
#         # ex: embeddings/chroma/420-111_exercices/
#         return BASE_DIR / "embeddings" / "chroma" / f"{self.module_code}_exercices"

#     @property
#     def chroma_collection(self) -> str:
#         return f"{self.module_code}_exercices"


# class RagRetriever:
#     """
#     Retriever hybride:
#     - priorité à Chroma (embeddings/chroma/{module}_exercices) si disponible
#     - sinon fallback sur embeddings .npy + texts .json (legacy)
#     """

#     def __init__(self, config: RagConfig, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
#         self.config = config
#         self.model_name = model_name

#         # ✅ si Chroma existe, on utilise Chroma
#         self.use_chroma = self.config.chroma_dir.exists()

#         # ---- Mode Chroma ----
#         self._chroma_client = None
#         self._chroma_col = None

#         # ---- Mode legacy ----
#         self.embeddings: Optional[np.ndarray] = None
#         self.docs: List[Dict[str, Any]] = []

#         if self.use_chroma:
#             self._init_chroma()
#         else:
#             self._init_legacy()

#     # -------------------------
#     # Chroma
#     # -------------------------
#     def _init_chroma(self) -> None:
#         # ouvrir la collection persistée
#         self._chroma_client = chromadb.PersistentClient(
#             path=str(self.config.chroma_dir),
#             settings=Settings(anonymized_telemetry=False),
#         )
#         self._chroma_col = self._chroma_client.get_collection(self.config.chroma_collection)

#         # embedder pour la requête
#         self.model = get_embedder(self.model_name)

#     # -------------------------
#     # Legacy npy/json
#     # -------------------------
#     def _init_legacy(self) -> None:
#         if not self.config.embeddings_path.exists():
#             raise FileNotFoundError(f"Embeddings introuvables: {self.config.embeddings_path}")

#         if not self.config.texts_path.exists():
#             raise FileNotFoundError(f"Texts introuvables: {self.config.texts_path}")

#         self.embeddings = np.load(self.config.embeddings_path).astype("float32")  # (N, d)

#         with open(self.config.texts_path, "r", encoding="utf-8") as f:
#             self.docs = json.load(f)  # [{"text":..., "metadata":...}, ...]

#         if len(self.docs) != self.embeddings.shape[0]:
#             raise ValueError(f"Incohérence: docs={len(self.docs)} vs embeddings={self.embeddings.shape[0]}")

#         # normaliser embeddings docs => cosinus = dot
#         norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
#         self.embeddings = self.embeddings / norms

#         # embedder requête
#         self.model = get_embedder(self.model_name)

#     # -------------------------
#     # Public API
#     # -------------------------
#     def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
#         query = (query or "").strip()
#         if not query:
#             return []

#         k = int(k or self.config.top_k)

#         t0 = time.perf_counter()

#         if self.use_chroma:
#             results = self._retrieve_chroma(query, k)
#         else:
#             results = self._retrieve_legacy(query, k)

#         retrieval_ms = (time.perf_counter() - t0) * 1000

#         # 🔎 debug perf (non bloquant)
#         st.session_state.setdefault("last_timing", {})
#         st.session_state["last_timing"]["retrieval_ms"] = round(retrieval_ms, 1)
#         st.session_state["last_timing"]["k"] = k
#         st.session_state["last_timing"]["retriever"] = "chroma" if self.use_chroma else "legacy"

#         return results


#     # -------------------------
#     # Retrieval implementations
#     # -------------------------
#     def _retrieve_chroma(self, query: str, k: int) -> List[Dict[str, Any]]:
#         assert self._chroma_col is not None

#         q_emb = self.model.encode([query]).tolist()[0]
#         res = self._chroma_col.query(query_embeddings=[q_emb], n_results=k)

#         docs = (res.get("documents") or [[]])[0]
#         metas = (res.get("metadatas") or [[]])[0]
#         dists = (res.get("distances") or [[]])[0]  # distance (plus petit = meilleur)

#         out: List[Dict[str, Any]] = []
#         for i in range(min(len(docs), len(metas))):
#             out.append({
#                 "text": docs[i] or "",
#                 "metadata": metas[i] or {},
#                 "score": float(-dists[i]) if i < len(dists) else 0.0,  # score approx (optionnel)
#             })
#         return out

#     def _retrieve_legacy(self, query: str, k: int) -> List[Dict[str, Any]]:
#         assert self.embeddings is not None

#         q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].astype("float32")
#         sims = self.embeddings @ q
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


from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import streamlit as st

import chromadb
from chromadb.config import Settings

from langchain_openai import OpenAIEmbeddings

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ cache global embeddings (évite de re-créer l'objet à chaque rerun)
_EMBEDDINGS: Optional[OpenAIEmbeddings] = None


def get_embeddings(model_name: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        _EMBEDDINGS = OpenAIEmbeddings(model=model_name)
    return _EMBEDDINGS


@dataclass
class RagConfig:
    module_code: str
    top_k: int = 4

    # Modèle d'embedding OpenAI (doit correspondre à celui utilisé pour créer Chroma / legacy)
    embedding_model: str = "text-embedding-3-small"

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
        return BASE_DIR / "embeddings" / "chroma" / f"{self.module_code}_exercices"

    @property
    def chroma_collection(self) -> str:
        return f"{self.module_code}_exercices"


class RagRetriever:
    """
    Retriever hybride:
    - priorité à Chroma (embeddings/chroma/{module}_exercices) si disponible
    - sinon fallback sur embeddings .npy + texts .json (legacy)

    ⚠️ IMPORTANT :
    Chroma / legacy doivent avoir été construits avec le MÊME modèle d'embeddings OpenAI,
    sinon il y aura un mismatch de dimensions.
    """

    def __init__(self, config: RagConfig):
        self.config = config

        # ✅ si Chroma existe, on utilise Chroma
        self.use_chroma = self.config.chroma_dir.exists()

        # ---- Mode Chroma ----
        self._chroma_client = None
        self._chroma_col = None

        # ---- Mode legacy ----
        self.embeddings: Optional[np.ndarray] = None
        self.docs: List[Dict[str, Any]] = []

        # ✅ embeddings OpenAI
        self.embeddings_fn = get_embeddings(self.config.embedding_model)

        if self.use_chroma:
            self._init_chroma()
        else:
            self._init_legacy()

    # -------------------------
    # Chroma
    # -------------------------
    def _init_chroma(self) -> None:
        self._chroma_client = chromadb.PersistentClient(
            path=str(self.config.chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._chroma_col = self._chroma_client.get_collection(self.config.chroma_collection)

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

        # ⚠️ Vérifier dimension
        try:
            q_dim = len(self.embeddings_fn.embed_query("probe dimension"))
        except Exception as e:
            raise RuntimeError(
                "Impossible de créer les embeddings OpenAI. Vérifie OPENAI_API_KEY dans Streamlit secrets."
            ) from e

        if self.embeddings.shape[1] != q_dim:
            raise ValueError(
                "Dimension mismatch entre les embeddings legacy et le modèle OpenAI.\n"
                f"- legacy .npy dim = {self.embeddings.shape[1]}\n"
                f"- OpenAI ({self.config.embedding_model}) dim = {q_dim}\n\n"
                "➡️ Solution: régénère tes embeddings legacy avec le même modèle OpenAI, "
                "ou utilise une collection Chroma construite avec ce modèle."
            )

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
        st.session_state["last_timing"]["embedding_model"] = self.config.embedding_model

        return results

    # -------------------------
    # Retrieval implementations
    # -------------------------
    def _retrieve_chroma(self, query: str, k: int) -> List[Dict[str, Any]]:
        assert self._chroma_col is not None

        q_emb = self.embeddings_fn.embed_query(query)
        res = self._chroma_col.query(query_embeddings=[q_emb], n_results=k)

        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]  # distance (plus petit = meilleur)

        out: List[Dict[str, Any]] = []
        for i in range(min(len(docs), len(metas))):
            out.append(
                {
                    "text": docs[i] or "",
                    "metadata": metas[i] or {},
                    "score": float(-dists[i]) if i < len(dists) else 0.0,
                }
            )
        return out

    def _retrieve_legacy(self, query: str, k: int) -> List[Dict[str, Any]]:
        assert self.embeddings is not None

        q_vec = np.array(self.embeddings_fn.embed_query(query), dtype="float32")
        q = q_vec / (np.linalg.norm(q_vec) + 1e-12)

        sims = self.embeddings @ q
        top_idx = np.argsort(-sims)[:k]

        results: List[Dict[str, Any]] = []
        for i in top_idx:
            d = self.docs[int(i)]
            results.append(
                {
                    "text": d.get("text", ""),
                    "metadata": d.get("metadata", {}),
                    "score": float(sims[int(i)]),
                }
            )
        return results
