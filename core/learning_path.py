# core/learning_path.py
from typing import Optional, Dict, Any
import streamlit as st

# ⚠️ adapte ces imports selon ton projet
from core.rag_retriever import get_retriever
from core.coach_rag import client  # là où tu as ton client OpenAI (comme dans generate_reply)


def generate_learning_path(module_label: str) -> str:
    """
    Génère une séquence d'apprentissage (parcours) basée sur les documents RAG du module.
    Met en cache par module pour éviter de régénérer à chaque rerun.
    """
    if not module_label:
        return "Choisis un cours avant de générer un parcours."

    module_code = module_label.split(" - ")[0].strip()

    # ✅ cache simple (par module)
    st.session_state.setdefault("learning_paths", {})
    if module_code in st.session_state["learning_paths"]:
        return st.session_state["learning_paths"][module_code]

    # 1) Récupérer des chunks orientés "structure/progression"
    TOPK_INTERNAL = 10
    retriever = get_retriever(module_code, TOPK_INTERNAL)

    query = (
        "Propose une progression d'apprentissage (séquence) pour ce cours : "
        "notions dans l'ordre, objectifs, prérequis, exercices conseillés."
    )

    hits = retriever.retrieve(query) or []
    if not hits:
        return "Je n’ai pas trouvé assez d’informations dans les documents pour proposer un parcours."

    context_text = "\n\n".join(
        "Titre: {title}\nSource: {source}\nContenu:\n{text}".format(
            title=h.get("metadata", {}).get("title", ""),
            source=h.get("metadata", {}).get("source", ""),
            text=(h.get("text", "")[:1400]),
        )
        for h in hits
    )

    prompt = f"""
Tu es EDUCARE, un tuteur pédagogique pour des étudiants en Techniques de l'informatique (cégep).
Tu dois proposer un PARCOURS D'APPRENTISSAGE pour le cours {module_label}.

Extraits disponibles :
{context_text}

Consignes (IMPORTANT) :
- Donne une séquence en 6 à 10 étapes maximum.
- Chaque étape : (1) objectif, (2) notions clés, (3) mini-activité/exercice conseillé.
- Simple, clair, structuré.
- Termine par "Sources :" avec 1 à 2 liens maximum (pris des extraits).
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Tu es un assistant pédagogique clair et structuré."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    out = (resp.choices[0].message.content or "").strip()

    # ✅ stocker en cache
    st.session_state["learning_paths"][module_code] = out
    return out
