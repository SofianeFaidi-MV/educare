# core/coach.py
from __future__ import annotations
from core.rag_retriever import RagRetriever, RagConfig
import time
import os
from typing import Optional

# Option LLM (facultative)
try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None  # type: ignore

import streamlit as st



from core.rag_retriever import EduCareRetriever, RagConfig

@st.cache_resource
def get_retriever_for_module(module_code: str) -> RagRetriever:
    # ⚠️ adapte si ton RagConfig utilise module_code (dans ton rag_retriever.py c’est module_code)
    return RagRetriever(RagConfig(module_code=module_code))

@st.cache_resource
def _get_retriever() -> EduCareRetriever:
    """
    Charge le retriever une seule fois (cache Streamlit).
    Ajuste ici les chemins si tu mets les fichiers dans /embeddings/.
    """
    cfg = RagConfig(
        embeddings_path="educare_embeddings.npy",
        texts_path="educare_texts.json",
        hf_model_name="sentence-transformers/all-MiniLM-L6-v2",
    )
    return EduCareRetriever(cfg)


def _build_prompt(module_title: str, question: str, docs: list[str]) -> str:
    context_block = "\n\n---\n\n".join(docs) if docs else "(aucun contexte trouvé)"
    return f"""Tu es EduCare, un coach d'apprentissage.
Cours sélectionné: {module_title}

Règles:
- Réponds en français.
- Utilise UNIQUEMENT le contexte fourni pour les faits (si le contexte ne suffit pas, dis-le).
- Sois clair, pédagogique, avec un mini-exemple si possible.

Contexte (extraits du cours/ressources):
{context_block}

Question de l'étudiant:
{question}

Réponse:
"""


# def generate_reply(user_text: str, context: Optional[dict] = None) -> str:
#     user_text = (user_text or "").strip()
#     if not user_text:
#         return "Écris une question et je t’aide 🙂"

#     context = context or {}
#     module_title = (context.get("selected_module_title") or context.get("module") or "Aucun cours sélectionné")

#     # 1) Retrieve
#     retriever = _get_retriever()
#     docs = retriever.similarity_search(f"{module_title}. {user_text}", k=4)

#     # 2) Si pas de clé API / pas de LLM, on renvoie une réponse "RAG-lite"
#     api_key_present = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY".lower()))
#     if ChatOpenAI is None or not api_key_present:
#         if not docs:
#             return (
#                 "Je n’ai pas trouvé de passage pertinent dans les ressources indexées pour répondre. "
#                 "Essaie de reformuler ou précise le concept (ex. « boucle for », « variables », etc.)."
#             )
#         # réponse “extractive” + guidage
#         bullets = "\n".join([f"- {d[:240].strip()}..." for d in docs])
#         return (
#             "Voici ce que j’ai trouvé dans les ressources (extraits) :\n"
#             f"{bullets}\n\n"
#             "Si tu veux, demande-moi ensuite : « explique-moi ça avec un exemple simple »."
#         )

#     # 3) Avec LLM (vrai RAG)
#     llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
#     prompt = _build_prompt(module_title, user_text, docs)
#     msg = llm.invoke(prompt)
#     return getattr(msg, "content", str(msg))


def generate_reply(user_input: str, context: dict):
    module = context.get("module")
    if not module:
        return "Veuillez sélectionner un cours."

    t0 = time.perf_counter()

    # ✅ 1) retriever (CACHÉ)
    t_init0 = time.perf_counter()
    retriever = get_retriever_for_module(module)
    init_ms = (time.perf_counter() - t_init0) * 1000

    # ✅ 2) retrieval
    t1 = time.perf_counter()
    docs = retriever.retrieve(user_input)
    retrieval_ms = (time.perf_counter() - t1) * 1000

    # ✅ 3) (option rapide) réduire docs envoyés au modèle
    docs = docs[:4]

    # ✅ 4) génération (probablement le plus long)
    t2 = time.perf_counter()
    answer = format_rag_answer(user_input, docs)
    generation_ms = (time.perf_counter() - t2) * 1000

    total_ms = (time.perf_counter() - t0) * 1000

    st.session_state.setdefault("last_timing", {})
    st.session_state["last_timing"].update({
        "init_retriever_ms": round(init_ms, 1),
        "retrieval_ms": round(retrieval_ms, 1),
        "generation_ms": round(generation_ms, 1),
        "total_ms": round(total_ms, 1),
        "k": len(docs),
    })

    return answer



