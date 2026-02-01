import streamlit as st

MODULES_RIGHT = [
    "420-411 - Interfaces humain-machine",
    "420-413 - Développement d'applications pour entreprise",
    "420-511 - Développement de jeux vidéo",
    "420-512 - Développement d'applications mobiles",
    "420-514 - Collecte et interprétation de données",
]

def render_right_panel():
    st.session_state.setdefault("selected_module", None)

    st.markdown('<div class="right-modules">', unsafe_allow_html=True)

    # ✅ bouton "Développer une compétence" (Streamlit -> Python)
    clicked_competence = st.button(
        "🎯 Développer une compétence",
        key="btn_competence_right",
        use_container_width=True,
    )

    # ✅ (optionnel) si tu veux AUSSI avoir le bouton Parcours à droite
    # clicked_path_right = st.button(
    #     "🎛️ Choisir un parcours d’apprentissage",
    #     key="btn_learning_path_right",
    #     use_container_width=True,
    # )
    clicked_path_right = False

    # modules (comme à gauche)
    for module_label in MODULES_RIGHT:
        is_selected = (st.session_state.selected_module == module_label)

        clicked = st.button(
            module_label,
            key=f"right_btn_{module_label}",
            use_container_width=True,
            disabled=is_selected,
        )
        if clicked:
            st.session_state.selected_module = module_label
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ✅ on retourne les clics pour que app.py pilote la suite
    return clicked_competence, clicked_path_right
