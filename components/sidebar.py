# import streamlit as st

# MODULES = [
#     "420-111 - Introduction à la programmation",
#     "420-112 - Création de sites web",
#     "420-210 - Programmation orientée-objet",
#     "420-211 - Applications Web",
#     "420-311 - Structures de données",
# ]

# def render_left_panel() -> None:
#     # ✅ wrapper indispensable (sinon le CSS .left-modules ne peut pas matcher)
#     st.markdown('<div class="left-modules">', unsafe_allow_html=True)

#     # Logo + marge via .logo-wrap
#     st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
#     st.image("static/educare_logo.png", width=120)
#     st.markdown('</div>', unsafe_allow_html=True)

#     for module_label in MODULES:
#         if st.button(
#             module_label,
#             key=f"left_module_btn_{module_label}",
#             use_container_width=True
#         ):
#             st.session_state.selected_module = module_label
#             st.query_params["tab"] = "parcours"
#             st.rerun()

#     # ✅ on ferme le wrapper qu’on a ouvert
#     st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st

MODULES_LEFT = [
    "420-111 - Introduction à la programmation",
    "420-112 - Création de sites web",
    "420-210 - Programmation orientée-objet",
    "420-211 - Applications Web",
    "420-311 - Structures de données",
]

def render_left_panel():
    st.session_state.setdefault("selected_module", None)

    st.markdown('<div class="left-modules">', unsafe_allow_html=True)

    # logo
    st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
    st.image("static/educare_logo.png", width=120)
    st.markdown("</div>", unsafe_allow_html=True)

    # ✅ bouton parcours (Streamlit -> Python)
    clicked_path = st.button(
        "🎛️ Choisir un parcours d’apprentissage",
        key="btn_learning_path_left",
        use_container_width=True,
    )

    # modules
    for module_label in MODULES_LEFT:
        is_selected = (st.session_state.selected_module == module_label)
        clicked = st.button(
            module_label,
            key=f"btn_{module_label}",
            use_container_width=True,
            disabled=is_selected,
        )
        if clicked:
            st.session_state.selected_module = module_label
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ✅ IMPORTANT: on retourne le clic
    return clicked_path



# def render_left_panel() -> None:
#     st.session_state.setdefault("selected_module", MODULES[0])  # ✅ jamais None

#     st.markdown('<div class="left-modules">', unsafe_allow_html=True)

#     st.markdown(
#         """
#         <div class="educare-header">
#             <img src="static/educare_logo.png" class="educare-logo">
#             <span class="educare-title">EduCare</span>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )

    

#     for module_label in MODULES:
#         is_selected = (st.session_state.selected_module == module_label)

#         clicked = st.button(
#             module_label,
#             key=f"btn_{module_label}",
#             use_container_width=True,
#             disabled=is_selected,   # ✅ sélection persistante
#         )

#         if clicked:
#             st.session_state.selected_module = module_label
#             st.rerun()

#     st.markdown('</div>', unsafe_allow_html=True)