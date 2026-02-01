# # # core/coach.py
# # from __future__ import annotations

# # import os
# # from pathlib import Path

# # from core.rag_retriever import RagRetriever, RagConfig


# # from typing import Optional, Dict, Any, List

# # # Ton retriever "maison" (selon où tu l'as placé)
# # try:
# #     from rag.retriever import EduCareRetriever  # si tu as un dossier rag/
# # except Exception:
# #     from retriever import EduCareRetriever      # si retriever.py est à la racine


# # BASE_DIR = Path(__file__).resolve().parent.parent
# # EMB_DIR = BASE_DIR / "embeddings"

# # SYSTEM_PROMPT = """Tu es EduCare, un coach pédagogique.
# # Réponds en français, de façon claire, avec exemples simples.
# # Si l'information n'est pas dans les extraits fournis, dis-le et propose quoi chercher.
# # """

# # def _format_sources(docs: List[str]) -> str:
# #     # Affiche des extraits courts
# #     out = []
# #     for i, d in enumerate(docs, 1):
# #         snippet = d.strip().replace("\n", " ")
# #         if len(snippet) > 280:
# #             snippet = snippet[:280] + "…"
# #         out.append(f"- Source {i} : {snippet}")
# #     return "\n".join(out)


# # def generate_reply(user_text: str, context: dict | None = None) -> str:
# #     user_text = (user_text or "").strip()
# #     if not user_text:
# #         return "Écris une question 🙂"

# #     module_label = (context or {}).get("module", "")
# #     if not module_label:
# #         return "Choisis un cours avant de poser ta question."

# #     # ✅ extrait "420-111" depuis "420-111 - Introduction à la programmation"
# #     module_code = module_label.split(" - ")[0].strip()

# #     retriever = RagRetriever(RagConfig(module_code=module_code, top_k=4))

# #     docs = retriever.retrieve(user_text)

# #     if not docs:
# #         return "Je n’ai rien trouvé dans les ressources de ce cours. Essaie de reformuler."

# #     # Réponse simple à partir des docs (sans LLM)
# #     answer = "Voici ce que j’ai trouvé :\n\n"
# #     for i, d in enumerate(docs, 1):
# #         answer += f"- ({i}) {d[:250]}...\n"
# #     return answer



# # # def generate_reply(user_text: str, context: Optional[Dict[str, Any]] = None) -> str:
# # #     user_text = (user_text or "").strip()
# # #     if not user_text:
# # #         return "Écris une question et je t’aide 🙂"

# # #     module = (context or {}).get("module")  # ex: "420-111 - Introduction à la programmation"
# # #     module_hint = f"[Cours: {module}] " if module else ""

# # #     # 1) Retrieval
# # #     retriever = EduCareRetriever(
# # #         embeddings_path=str(EMB_DIR / "educare_embeddings.npy"),
# # #         texts_path=str(EMB_DIR / "educare_texts.json"),
# # #     )
# # #     docs = retriever.similarity_search(module_hint + user_text, k=4)

# # #     # 2) Si pas de LLM -> réponse “RAG-lite”
# # #     if not os.getenv("OPENAI_API_KEY"):
# # #         return (
# # #             f"Voici ce que j’ai trouvé dans tes ressources pour répondre à : « {user_text} »\n\n"
# # #             f"{_format_sources(docs)}\n\n"
# # #             "👉 Si tu veux, je peux ensuite te faire une explication complète (définition + exemple de code), "
# # #             "mais il me faut plus de contenu indexé (plus de pages/chapitres)."
# # #         )

# # #     # 3) Si tu as une clé OpenAI -> vraie réponse rédigée à partir des sources
# # #     from langchain_openai import ChatOpenAI

# # #     llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# # #     context_block = "\n\n".join([f"[Doc {i+1}] {d}" for i, d in enumerate(docs)])
# # #     prompt = f"""{SYSTEM_PROMPT}

# # # Extraits de cours (à utiliser comme seule source de contenu) :
# # # {context_block}

# # # Question de l'étudiant : {user_text}

# # # Réponds en t'appuyant sur les extraits.
# # # """

# # #     msg = llm.invoke(prompt)
# # #     answer = getattr(msg, "content", str(msg)).strip()

# # #     return answer


# # core/coach.py
# from __future__ import annotations
# from typing import Any, Dict, Optional
# import os

# from core.rag_retriever import RagRetriever, RagConfig
# from openai import OpenAI
# import streamlit as st
# from core.empathy_module import EmpathyModule


# # Initialiser le client OpenAI une seule fois
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# empathy = EmpathyModule()


# def generate_reply(user_text: str, context: Optional[Dict[str, Any]] = None) -> str:
#     # 🔹 0) Normalisation
#     user_text = (user_text or "").strip()
#     if not user_text:
#         return "Écris une question 🙂"

#     module_label = (context or {}).get("module", "")
#     if not module_label:
#         return "Choisis un cours avant de poser une question."

#     # ✅ état: question “en attente de clarification”
#     st.session_state.setdefault("pending_clarification", None)

#     # 🔹 CAS A) On attend une confirmation/reformulation
#     pending = st.session_state.get("pending_clarification")
#     if pending:
#         ans = user_text.lower().strip()

#         if ans in {"oui", "yes", "ouais", "ok", "d'accord", "daccord"}:
#             # ✅ l'utilisateur confirme : on remplace par la vraie question
#             user_text = pending
#             st.session_state["pending_clarification"] = None

#         elif ans in {"non", "no", "nop"}:
#             st.session_state["pending_clarification"] = None
#             return "D’accord 🙂 Peux-tu reformuler ta question ?"

#         else:
#             # ✅ l'utilisateur reformule directement : on garde son texte
#             st.session_state["pending_clarification"] = None
#             # user_text reste tel quel (sa reformulation)

#     # 🔴 CAS B) Filtre linguistique AVANT le RAG
#     lowered = user_text.lower()
#     # 🔹 Détection "demande sur exercices" (heuristique simple)
#     EXO_HINTS = ("exercice", "série", "serie", "consigne", "énoncé", "enonce", "tp", "devoir", "question", "indice", "hint")
#     is_exercise_request = any(k in lowered for k in EXO_HINTS)


#     if "breivement" in lowered:
#         # ✅ on stocke une question “interprétée” à réutiliser si l'utilisateur répond "oui"
#         st.session_state["pending_clarification"] = (
#             "Peux-tu expliquer brièvement ce qu’est une fonction en programmation ?"
#         )
#         return (
#             "Veux-tu dire **« brièvement »** (expliquer rapidement) ? 🤔\n\n"
#             "👉 Réponds **oui** pour continuer, ou reformule ta question.\n\n"
#             "Exemple : *Peux-tu expliquer brièvement ce qu’est une fonction ?*"
#         )

#     # ex: "420-111 - Introduction à la programmation" -> "420-111"
#     module_code = module_label.split(" - ")[0].strip()

#     # 🔹 1) RAG
#     retriever = RagRetriever(RagConfig(module_code=module_code, top_k=2))
#     hits = retriever.retrieve(user_text)
#     has_exos = any(h.get("metadata", {}).get("corpus") == "exercices" for h in hits)

#     # 🔹 Si l'utilisateur parle d'exercices, on priorise les chunks "exercices"
#     if is_exercise_request:
#         exo_hits = [h for h in hits if h.get("metadata", {}).get("corpus") == "exercices"]
#         if exo_hits:
#             hits = exo_hits + [h for h in hits if h not in exo_hits]


#     if not hits:
#         return (
#             "Je ne suis pas certain de bien comprendre ta question 🤔\n\n"
#             "👉 Peux-tu la reformuler ou être un peu plus précis ?"
#         )

#     # 🔹 2) Construire le contexte
#     context_text = "\n\n".join(
#         f"Titre: {h['metadata'].get('title','')}\n"
#         f"Source: {h['metadata'].get('source','')}\n"
#         f"Contenu:\n{h['text']}"
#         for h in hits
#     )

#     # 🔹 3) Prompt pédagogique
# #     prompt = f"""
# # Tu es un tuteur pédagogique pour des étudiants débutants en programmation (cégep).
# # Réponds en français clair, simple et structuré.
# # Si un mot semble incorrect, ambigu ou non reconnu,
# # ne pas inventer de concept.
# # Toujours demander une clarification.

# # Question de l'étudiant :
# # {user_text}

# # Extraits du cours (à utiliser uniquement si pertinent) :
# # {context_text}

# # Contraintes :
# # - 6 à 8 lignes maximum
# # - vocabulaire simple
# # - si pertinent, un mini-exemple Java (1–2 lignes)
# # - si la question est ambiguë ou incorrecte, demande une clarification
# # - termine par "Sources :" avec 1 ou 2 liens maximum
# # """

#     mode_block = ""
#     if is_exercise_request:
#         mode_block = """
#     MODE EXERCICE (IMPORTANT) :
#     - Donne uniquement un INDICE + une STRATÉGIE de résolution.
#     - Ne donne pas la solution complète, ni un code complet.
#     - Tu peux fournir 1 à 3 lignes de pseudo-code OU 1 à 2 lignes de Java maximum.
#     - Si l'énoncé n'est pas assez précis, demande l'énoncé exact ou la partie qui bloque.
#     - Propose une démarche: (1) comprendre l'entrée/sortie, (2) choisir structures, (3) tester avec un exemple.
#     - Encourage l'étudiant à essayer une étape et revenir avec son code.
#     """
#     else:
#         mode_block = """
#     MODE COURS :
#     - Explique le concept simplement.
#     - Donne un mini-exemple (1–2 lignes Java) si pertinent.
#     """

#     prompt = f"""
#     Tu es EDUCARE, un tuteur pédagogique pour des étudiants débutants en programmation (cégep).
#     Réponds en français clair, simple et structuré.

#     {mode_block}

#     Question de l'étudiant :
#     {user_text}

#     Extraits du cours (tu dois t'appuyer sur ces extraits, et ne pas inventer) :
#     {context_text}

#     Contraintes de forme :
#     - 6 à 10 lignes maximum
#     - vocabulaire simple
#     - si la question est ambiguë : demande une clarification
#     - termine par "Sources :" avec 1 ou 2 liens maximum (provenant des extraits)
#     """


#     # 🔹 4) Appel LLM
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "Tu es un assistant pédagogique concis."},
#             {"role": "user", "content": prompt},
#         ],
#         temperature=0.2,
#     )

#     answer = response.choices[0].message.content.strip()


#     # 🔹 4.5) Module empathique (post-traitement : forme, pas contenu)
#     answer, empathy_decision = empathy.run(user_text=user_text, rag_answer=answer)

#     # (Optionnel) log minimal pour l'évaluation (sans texte)
#     st.session_state.setdefault("empathy_logs", []).append({
#         "module": module_code,
#         "mode": empathy_decision.mode.value,
#         "intensity": float(empathy_decision.intensity),
#         "n_signals": len(empathy_decision.signals),
#     })


#     # 🔹 5) Sécurité sources
#     if "Sources" not in answer:
#         sources = "\n".join(
#             {h["metadata"].get("source", "") for h in hits if h["metadata"].get("source", "")}
#         )
#         if sources:
#             answer += "\n\nSources :\n" + sources

#     return answer

# core/coach.py
# from __future__ import annotations

# from typing import Any, Dict, Optional, List
# import os

# import streamlit as st
# from openai import OpenAI

# from core.rag_retriever import RagRetriever, RagConfig
# from core.empathy_module import EmpathyModule


# # ✅ Initialiser le client OpenAI une seule fois
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# # ✅ Module empathique (post-traitement : forme, pas contenu)
# empathy = EmpathyModule()


# def _detect_exercise_request(user_text: str) -> bool:
#     """Heuristique simple : l'utilisateur parle-t-il d'exercices / labo / indice ?"""
#     lowered = (user_text or "").lower()
#     EXO_HINTS = (
#         "exercice", "exercices",
#         "série", "serie", "séries", "series",
#         "consigne", "énoncé", "enonce",
#         "tp", "labo", "lab",
#         "devoir",
#         "question",
#         "indice", "hint",
#         "corrigé", "correction",
#     )
#     return any(k in lowered for k in EXO_HINTS)


# def _prioritize_hits(
#     hits: List[Dict[str, Any]],
#     is_exercise_request: bool,
#     exo_first_k: int = 3,
#     cours_first_k: int = 3,
#     secondary_k: int = 2,
# ) -> tuple[List[Dict[str, Any]], bool]:
#     """
#     Sépare cours/exercices via metadata['corpus'] puis applique une stratégie :
#     - si demande exercice -> exos d'abord
#     - sinon -> cours d'abord
#     Retourne (hits_selectionnés, has_exos).
#     """
#     exo_hits = [h for h in hits if h.get("metadata", {}).get("corpus") == "exercices"]
#     cours_hits = [h for h in hits if h.get("metadata", {}).get("corpus") != "exercices"]

#     has_exos = len(exo_hits) > 0

#     if is_exercise_request:
#         selected = exo_hits[:exo_first_k] + cours_hits[:secondary_k]
#     else:
#         selected = cours_hits[:cours_first_k] + exo_hits[:secondary_k]

#     # fallback : si sélection vide, on garde ce qu'on a
#     if not selected:
#         selected = hits

#     return selected, has_exos


# def generate_reply(user_text: str, context: Optional[Dict[str, Any]] = None) -> str:
#     # 🔹 0) Normalisation
#     user_text = (user_text or "").strip()
#     if not user_text:
#         return "Écris une question 🙂"

#     module_label = (context or {}).get("module", "")
#     if not module_label:
#         return "Choisis un cours avant de poser une question."

#     # ✅ état: question “en attente de clarification”
#     st.session_state.setdefault("pending_clarification", None)

#     # 🔹 CAS A) On attend une confirmation/reformulation
#     pending = st.session_state.get("pending_clarification")
#     if pending:
#         ans = user_text.lower().strip()

#         if ans in {"oui", "yes", "ouais", "ok", "d'accord", "daccord"}:
#             # ✅ l'utilisateur confirme : on remplace par la vraie question
#             user_text = pending
#             st.session_state["pending_clarification"] = None

#         elif ans in {"non", "no", "nop"}:
#             st.session_state["pending_clarification"] = None
#             return "D’accord 🙂 Peux-tu reformuler ta question ?"

#         else:
#             # ✅ l'utilisateur reformule directement : on garde son texte
#             st.session_state["pending_clarification"] = None
#             # user_text reste tel quel (sa reformulation)

#     # 🔴 CAS B) Filtre linguistique AVANT le RAG (exemple)
#     lowered = user_text.lower()
#     if "breivement" in lowered:
#         st.session_state["pending_clarification"] = (
#             "Peux-tu expliquer brièvement ce qu’est une fonction en programmation ?"
#         )
#         return (
#             "Veux-tu dire **« brièvement »** (expliquer rapidement) ? 🤔\n\n"
#             "👉 Réponds **oui** pour continuer, ou reformule ta question.\n\n"
#             "Exemple : *Peux-tu expliquer brièvement ce qu’est une fonction ?*"
#         )

#     # 🔹 Détection "demande exercice" côté utilisateur
#     is_exercise_request = _detect_exercise_request(user_text)

#     # ex: "420-111 - Introduction à la programmation" -> "420-111"
#     module_code = module_label.split(" - ")[0].strip()

#     # 🔹 1) RAG (⚠️ top_k plus élevé pour capter exos + cours)
#     retriever = RagRetriever(RagConfig(module_code=module_code, top_k=8))
#     hits = retriever.retrieve(user_text)

#     if not hits:
#         return (
#             "Je ne suis pas certain de bien comprendre ta question 🤔\n\n"
#             "👉 Peux-tu la reformuler ou être un peu plus précis ?"
#         )

#     # 🔹 1.1) Prioriser les chunks (cours/exercices) selon le besoin
#     hits, has_exos = _prioritize_hits(hits, is_exercise_request=is_exercise_request)

#     # 🔹 2) Construire le contexte (cours + exercices)
#     context_text = "\n\n".join(
#         "Titre: {title}\nSource: {source}\nContenu:\n{text}".format(
#             title=h.get("metadata", {}).get("title", ""),
#             source=h.get("metadata", {}).get("source", ""),
#             text=h.get("text", ""),
#         )
#         for h in hits
#     )

#     # 🔹 3) Choisir le mode : basé sur les sources récupérées (priorité) + intention user
#     mode_is_exo = has_exos or is_exercise_request

#     mode_block = """
# MODE EXERCICE (IMPORTANT) :
# - Ne donne PAS la solution complète.
# - Donne 1 à 3 indices progressifs (du plus général au plus concret).
# - Rappelle le concept clé à revoir.
# - Pose une mini-question pour guider l’étudiant.
# - Si l’étudiant insiste : propose un plan de résolution (pas le code final).
# - Tu peux donner 0 à 2 lignes de pseudo-code OU 1 à 2 lignes de Java maximum si nécessaire.
# - Si l’énoncé est incomplet : demande l’énoncé exact ou la partie qui bloque.
# """ if mode_is_exo else """
# MODE COURS :
# - Explique le concept simplement.
# - Donne un exemple très court (1–2 lignes) si pertinent.
# - Si un terme est ambigu : demande une clarification plutôt que d’inventer.
# """

#     # 🔹 4) Prompt
#     prompt = f"""
# Tu es EDUCARE, un tuteur pédagogique pour des étudiants en Techniques de l'informatique (cégep).
# Réponds en français clair, simple et structuré.

# {mode_block}

# Question de l'étudiant :
# {user_text}

# Extraits (cours + exercices) :
# {context_text}

# Contraintes de forme :
# - 8 à 12 lignes maximum
# - vocabulaire simple
# - si la question est ambiguë : demande une clarification
# - termine par "Sources :" avec 1 à 2 liens maximum (provenant des extraits)
# """

#     # 🔹 5) Appel LLM
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "Tu es un assistant pédagogique concis et bienveillant."},
#             {"role": "user", "content": prompt},
#         ],
#         temperature=0.2,
#     )

#     answer = response.choices[0].message.content.strip()

#     # 🔹 6) Module empathique (post-traitement : forme, pas contenu)
#     answer, empathy_decision = empathy.run(user_text=user_text, rag_answer=answer)

#     # (Optionnel) log minimal pour l'évaluation (sans stocker de texte)
#     st.session_state.setdefault("empathy_logs", []).append({
#         "module": module_code,
#         "mode": getattr(empathy_decision, "mode", None).value if getattr(empathy_decision, "mode", None) else None,
#         "intensity": float(getattr(empathy_decision, "intensity", 0.0)),
#         "n_signals": len(getattr(empathy_decision, "signals", [])),
#         "mode_is_exo": bool(mode_is_exo),
#         "has_exos": bool(has_exos),
#         "is_exercise_request": bool(is_exercise_request),
#     })

#     # 🔹 7) Sécurité sources (ajoute des liens si le LLM a oublié)
#     if "Sources" not in answer:
#         sources = "\n".join(
#             {h.get("metadata", {}).get("source", "") for h in hits if h.get("metadata", {}).get("source", "")}
#         )
#         if sources.strip():
#             answer += "\n\nSources :\n" + sources

#     return answer


from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import os
import time

import streamlit as st
from openai import OpenAI

from core.rag_retriever import RagRetriever, RagConfig
from core.empathy_module import EmpathyModule


# ✅ Initialiser le client OpenAI une seule fois
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ✅ Module empathique (post-traitement : forme, pas contenu)
empathy = EmpathyModule()


def _detect_exercise_request(user_text: str) -> bool:
    """Heuristique simple : l'utilisateur parle-t-il d'exercices / labo / indice ?"""
    lowered = (user_text or "").lower()
    EXO_HINTS = (
        "exercice", "exercices",
        "série", "serie", "séries", "series",
        "consigne", "énoncé", "enonce",
        "tp", "labo", "lab",
        "devoir",
        "question",
        "indice", "hint",
        "corrigé", "correction",
    )
    return any(k in lowered for k in EXO_HINTS)


def _prioritize_hits(
    hits: List[Dict[str, Any]],
    is_exercise_request: bool,
    exo_first_k: int = 3,
    cours_first_k: int = 3,
    secondary_k: int = 2,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Sépare cours/exercices via metadata['corpus'] puis applique une stratégie :
    - si demande exercice -> exos d'abord
    - sinon -> cours d'abord
    Retourne (hits_selectionnés, has_exos).
    """
    exo_hits = [h for h in hits if h.get("metadata", {}).get("corpus") == "exercices"]
    cours_hits = [h for h in hits if h.get("metadata", {}).get("corpus") != "exercices"]

    has_exos = len(exo_hits) > 0

    if is_exercise_request:
        selected = exo_hits[:exo_first_k] + cours_hits[:secondary_k]
    else:
        selected = cours_hits[:cours_first_k] + exo_hits[:secondary_k]

    if not selected:
        selected = hits

    return selected, has_exos


# ✅ Cache du retriever par module (évite reload embeddings à chaque question)
@st.cache_resource(show_spinner=False)
def get_retriever(module_code: str, top_k: int) -> RagRetriever:
    return RagRetriever(RagConfig(module_code=module_code, top_k=top_k))


def _clip(text: str, max_chars: int = 1400) -> str:
    """Réduit le contexte envoyé au LLM pour baisser la latence et les tokens."""
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= max_chars else (text[:max_chars] + "…")


def generate_reply(user_text: str, context: Optional[Dict[str, Any]] = None) -> str:
    t0 = time.perf_counter()

    # 🔹 0) Normalisation
    user_text = (user_text or "").strip()
    if not user_text:
        return "Écris une question 🙂"

    module_label = (context or {}).get("module", "")
    if not module_label:
        return "Choisis un cours avant de poser une question."

    # ✅ état: question “en attente de clarification”
    st.session_state.setdefault("pending_clarification", None)

    # 🔹 CAS A) On attend une confirmation/reformulation
    pending = st.session_state.get("pending_clarification")
    if pending:
        ans = user_text.lower().strip()

        if ans in {"oui", "yes", "ouais", "ok", "d'accord", "daccord"}:
            user_text = pending
            st.session_state["pending_clarification"] = None

        elif ans in {"non", "no", "nop"}:
            st.session_state["pending_clarification"] = None
            return "D’accord 🙂 Peux-tu reformuler ta question ?"

        else:
            st.session_state["pending_clarification"] = None

    # 🔴 CAS B) Filtre linguistique AVANT le RAG (exemple)
    lowered = user_text.lower()
    if "breivement" in lowered:
        st.session_state["pending_clarification"] = (
            "Peux-tu expliquer brièvement ce qu’est une fonction en programmation ?"
        )
        return (
            "Veux-tu dire **« brièvement »** (expliquer rapidement) ? 🤔\n\n"
            "👉 Réponds **oui** pour continuer, ou reformule ta question.\n\n"
            "Exemple : *Peux-tu expliquer brièvement ce qu’est une fonction ?*"
        )

    # 🔹 Détection "demande exercice" côté utilisateur
    is_exercise_request = _detect_exercise_request(user_text)

    # ex: "420-111 - Introduction à la programmation" -> "420-111"
    module_code = module_label.split(" - ")[0].strip()



    # 🔹 ROUTAGE : requêtes trop courtes/ambiguës
    q = user_text.lower().strip()
    words = [w for w in q.split() if w]

    # (A) "intro" / "introduction" -> forcer une intention "cours"
    if q in {"intro", "introduction"}:
        # Option 1 (recommandée) : demander précision
        st.session_state["pending_clarification"] = user_text
        return (
            "Quand tu dis **« intro »**, tu veux plutôt :\n"
            "1) l’introduction **du cours** (concepts, objectifs)\n"
            "2) l’introduction **des exercices**\n\n"
            "Réponds **1** ou **2** 🙂"
        )

    # (B) Si l'utilisateur répond 1 ou 2 après clarification
    pending = st.session_state.get("pending_clarification")
    if pending and q in {"1", "2"}:
        st.session_state["pending_clarification"] = None
        if q == "1":
            # on enrichit la requête pour pousser vers les pages cours
            user_text = "introduction du cours programmation concepts de base objectifs"
        else:
            user_text = "introduction des exercices consignes exercices programmation"

    # 🔹 1) RAG
    # ⚠️ top_k interne pour récupérer assez de chunks, puis on sélectionne
    TOPK_INTERNAL = 8

    t_rag0 = time.perf_counter()
    retriever = get_retriever(module_code, TOPK_INTERNAL)
    hits = retriever.retrieve(user_text)
    t_rag = time.perf_counter() - t_rag0

    if not hits:
        st.session_state["last_latency"] = {
            "total_s": round(time.perf_counter() - t0, 2),
            "rag_s": round(t_rag, 2),
            "llm_s": 0.0,
            "n_hits": 0,
        }
        return (
            "Je ne suis pas certain de bien comprendre ta question 🤔\n\n"
            "👉 Peux-tu la reformuler ou être un peu plus précis ?"
        )

    # 🔹 1.1) Prioriser les chunks (cours/exercices) selon le besoin
    hits, has_exos = _prioritize_hits(hits, is_exercise_request=is_exercise_request)

  # ✅ MODE EXO seulement si l'intention user le demande
    mode_is_exo = bool(is_exercise_request and has_exos)


    # 🔹 2) Construire le contexte (limité pour latence/tokens)
    t_ctx0 = time.perf_counter()
    context_text = "\n\n".join(
        "Titre: {title}\nSource: {source}\nContenu:\n{text}".format(
            title=h.get("metadata", {}).get("title", ""),
            source=h.get("metadata", {}).get("source", ""),
            text=_clip(h.get("text", ""), 1400),
        )
        for h in hits
    )
    t_ctx = time.perf_counter() - t_ctx0

    # 🔹 3) Choisir le mode : basé sur les sources récupérées + intention user
    mode_is_exo = has_exos or is_exercise_request

    mode_block = """
MODE EXERCICE (IMPORTANT) :
- Ne donne PAS la solution complète.
- Donne 1 à 3 indices progressifs (du plus général au plus concret).
- Rappelle le concept clé à revoir.
- Pose une mini-question pour guider l’étudiant.
- Si l’étudiant insiste : propose un plan de résolution (pas le code final).
- Tu peux donner 0 à 2 lignes de pseudo-code OU 1 à 2 lignes de Java maximum si nécessaire.
- Si l’énoncé est incomplet : demande l’énoncé exact ou la partie qui bloque.
""" if mode_is_exo else """
MODE COURS :
- Explique le concept simplement.
- Donne un exemple très court (1–2 lignes) si pertinent.
- Si un terme est ambigu : demande une clarification plutôt que d’inventer.
"""

    # 🔹 4) Prompt
    t_prompt0 = time.perf_counter()
    prompt = f"""
Tu es EDUCARE, un tuteur pédagogique pour des étudiants en Techniques de l'informatique (cégep).
Réponds en français clair, simple et structuré.

{mode_block}

Question de l'étudiant :
{user_text}

Extraits (cours + exercices) :
{context_text}

Contraintes de forme :
- 8 à 12 lignes maximum
- vocabulaire simple
- si la question est ambiguë : demande une clarification
- termine par "Sources :" avec 1 à 2 liens maximum (provenant des extraits)
"""
    t_prompt = time.perf_counter() - t_prompt0

    # 🔹 5) Appel LLM
    t_llm0 = time.perf_counter()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Tu es un assistant pédagogique concis et bienveillant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    t_llm = time.perf_counter() - t_llm0

    answer = (response.choices[0].message.content or "").strip()

    # 🔹 6) Module empathique (post-traitement : forme, pas contenu)
    t_emp0 = time.perf_counter()
    answer, empathy_decision = empathy.run(user_text=user_text, rag_answer=answer)
    t_emp = time.perf_counter() - t_emp0

    # ✅ Latence : stocker les timings (diagnostic)
    t_total = time.perf_counter() - t0
    st.session_state["last_latency"] = {
        "total_s": round(t_total, 2),
        "rag_s": round(t_rag, 2),
        "ctx_s": round(t_ctx, 3),
        "prompt_s": round(t_prompt, 3),
        "llm_s": round(t_llm, 2),
        "empathy_s": round(t_emp, 3),
        "n_hits": len(hits),
        "mode_is_exo": bool(mode_is_exo),
    }

    # (Optionnel) log minimal pour l'évaluation (sans stocker de texte)
    st.session_state.setdefault("empathy_logs", []).append({
        "module": module_code,
        "mode": getattr(empathy_decision, "mode", None).value if getattr(empathy_decision, "mode", None) else None,
        "intensity": float(getattr(empathy_decision, "intensity", 0.0)),
        "n_signals": len(getattr(empathy_decision, "signals", [])),
        "mode_is_exo": bool(mode_is_exo),
        "has_exos": bool(has_exos),
        "is_exercise_request": bool(is_exercise_request),
    })

    # 🔹 7) Sécurité sources (ajoute des liens si le LLM a oublié)
    if "Sources" not in answer:
        sources = "\n".join(
            {h.get("metadata", {}).get("source", "") for h in hits if h.get("metadata", {}).get("source", "")}
        )
        if sources.strip():
            answer += "\n\nSources :\n" + sources

    return answer