import streamlit as st

def init_state() -> None:
    # module sélectionné (unifier avec le reste du projet)
    st.session_state.setdefault("selected_module", None)

    # ancien champ (si tu l’utilises ailleurs)
    st.session_state.setdefault("module", "Introduction à la programmation")

    # navigation bas
    st.session_state.setdefault("bottom_tab", "Choisir un parcours d’apprentissage")

    # input chat (unifier)
    st.session_state.setdefault("chat_input_main", "")
    st.session_state.setdefault("chat_input", "")  # si ancien code encore présent

    # ✅ historique chat (pour afficher user + assistant)
    st.session_state.setdefault("chat_messages", [
        {"role": "assistant", "text": "Salut 👋 Je suis EduCare, ton coach d’apprentissage."},
        {"role": "assistant", "text": "1) Commence par choisir un cours à gauche ou à droite."},
        {"role": "assistant", "text": "2) Ensuite, écris ta question dans la zone de chat."},
        {"role": "assistant", "text": "Exemples : « Explique-moi les boucles » ou « Donne-moi un exercice sur les listes »."},
    ])
