import streamlit as st
from core.coach import generate_reply
from core.progression import log_question, save_progress
from core.badges import update_badges



def render_center_area() -> None:
    # -------------------------
    # 0) Placeholder dynamique
    # -------------------------
    selected = st.session_state.get("selected_module")
    placeholder = (
        "💬 Le progrès commence par une question."
        if not selected
        else f"💬 Pose ta question sur : {selected}"
    )

    # -------------------------
    # 1) Formulaire de saisie
    # -------------------------
    disabled = bool(st.session_state.get("_busy", False))

    with st.form("educare_chat_form", clear_on_submit=True):
        user_text = st.text_area(
            "",
            key="chat_input_main",
            height=110,
            placeholder=placeholder,
            disabled=disabled,
        )
        submitted = st.form_submit_button("Envoyer", disabled=disabled)

    # -------------------------
    # 2) Envoi + réponse (1 seul appel LLM)
    # -------------------------
    if submitted:
        user_text = (user_text or "").strip()

        # A) module non sélectionné
        if not selected:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "text": "👈 Choisis d’abord un cours (à gauche ou à droite), puis repose ta question."
            })
            st.rerun()

        # B) input vide
        if not user_text:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "text": "Écris une question et je t’aide 🙂"
            })
            st.rerun()

        # C) anti-double appel (important)
        if st.session_state.get("_busy", False):
            # Si un appel est déjà en cours, on ne fait rien
            st.stop()

        st.session_state["_busy"] = True
        try:
            # 1) message utilisateur
            st.session_state.chat_messages.append({"role": "user", "text": user_text})

            # 2) tracking progression
            progress = st.session_state.get("progress")
            if progress:
                log_question(progress, selected)
                update_badges(progress)
                save_progress(progress, user_id="default")

            # 3) appel RAG + modèle (là où ça prend du temps)
            # with st.spinner("EduCare réfléchit…"):
            reply = generate_reply(user_text, context={"module": selected})

            # 4) message assistant
            st.session_state.chat_messages.append({"role": "assistant", "text": reply})

        except Exception as e:
            # Message utilisateur-friendly + debug minimal
            st.session_state.chat_messages.append({
                "role": "assistant",
                "text": "⚠️ Désolé, j’ai rencontré une erreur en générant la réponse. Réessaie."
            })
            # optionnel: log console
            print("Erreur generate_reply:", repr(e))

        finally:
            st.session_state["_busy"] = False

        st.rerun()

    # -------------------------
    # 3) Zone chat (rendu via inject_intro_bot() dans app.py)
    # -------------------------
    st.markdown('<div class="bigarea"><div id="intro-bot"></div></div>', unsafe_allow_html=True)

    # -------------------------
    # (Optionnel) Debug perf dans la sidebar
    # -------------------------
    # with st.sidebar:
    #     st.json(st.session_state.get("last_timing", {}))





# def on_send_question():
#     q = (st.session_state.get("chat_input_main") or "").strip()
#     if not q:
#         return

#     module = st.session_state.get("selected_module")

#     if not module:
#         st.session_state.chat_messages.append({
#             "role": "assistant",
#             "text": "Choisis d’abord un cours à gauche ou à droite 🙂"
#         })
#         st.session_state.chat_input_main = ""
#         return

#     st.session_state.chat_messages.append({"role": "user", "text": q})
#     st.session_state.chat_messages.append({
#         "role": "assistant",
#         "text": f"(Cours : {module}) Voici une réponse à ta question : « {q} »."
#     })

#     st.session_state.chat_input_main = ""


# def render_center_area():
#     # init messages UNE SEULE FOIS
#     st.session_state.setdefault("chat_messages", [
#         {"role": "assistant", "text": "Salut 👋 Je suis EduCare, ton coach d’apprentissage."},
#         {"role": "assistant", "text": "1) Commence par choisir un cours à gauche ou à droite."},
#         {"role": "assistant", "text": "2) Ensuite, écris ta question dans la zone de chat."},
#         {"role": "assistant", "text": "Exemples : « Explique-moi les boucles » ou « Donne-moi un exercice sur les listes »."},
#     ])

#     # 🟩 ZONE VERTE
#     st.markdown('<div class="bigarea">', unsafe_allow_html=True)

#     # 🔹 MESSAGES (DANS la bigarea)
#     st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
#     for m in st.session_state.chat_messages:
#         cls = "user-bubble" if m["role"] == "user" else "bot-bubble"
#         st.markdown(f'<div class="{cls}">{m["text"]}</div>', unsafe_allow_html=True)
#     st.markdown('</div>', unsafe_allow_html=True)

#     # 🔹 INPUT (DANS la bigarea, en bas)
#     st.markdown('<div class="chat-input">', unsafe_allow_html=True)
#     with st.form("chat_form", clear_on_submit=False):
#         st.text_area(
#             "",
#             key="chat_input_main",
#             placeholder="Le progrès commence par une question.",
#             label_visibility="collapsed",
#             height=90
#         )
#         st.form_submit_button("Envoyer", on_click=on_send_question)
#     st.markdown('</div>', unsafe_allow_html=True)

#     st.markdown('</div>', unsafe_allow_html=True)





    # Exemple de génération (optionnel: décommente si tu veux afficher une réponse)
    # if st.session_state.chat_input.strip():
    #     st.info(generate_reply(st.session_state.chat_input, context={"module": st.session_state.module}))
