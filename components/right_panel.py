# # import streamlit as st

# # MODULES = [
# #     # "420-111 - Introduction à la programmation",
# #     # "420-112 - Création de sites web",
# #     # "420-113 - Systèmes d'exploitation",

# #     # "420-210 - Programmation orientée-objet",    
# #     # "420-211 - Applications Web",
# #     # "420-212 - Introduction aux bases de données",
    

# #     # "420-310 - Architecture de logiciel",
# #     # "420-311 - Structures de données",
# #     # "420-312 - Conception de réseaux informatiques",
# #     # "420-313 - Sécurité informatique ",
# #     # "420-314 - Programmation de plateformes embarquées",

# #     # "420-410 - Introduction aux plateformes IdO",
# #     # "420-411 - Interfaces humain-machine ",
# #     # "420-412 - Projet - Développement d'une application Web",
# #     # "420-413 - Développement d'applications pour entreprise",
# #     # "420-414 - Infonuagique",
    
# #     # "420-510 - Soutien informatique",
# #     # "420-511 - Développement de jeux vidéo",
# #     # "420-512 - Développement d'applications mobiles",
# #     # "420-513 - Piratage éthique",
# #     # "420-514 - Collecte et interprétation de données",
# #     # "420-515 - Maintenance de logiciel",

# #     "420-411 - Interfaces humain-machine ",
# #     "420-413 - Développement d'applications pour entreprise",
# #     "420-511 - Développement de jeux vidéo",
# #     "420-512 - Développement d'applications mobiles",
# #     "420-514 - Collecte et interprétation de données",
# # ]

# # def render_right_panel() -> None:
# #     st.markdown('<div class="right-modules">', unsafe_allow_html=True)

# #     for i, m in enumerate(MODULES):
# #         st.markdown(
# #             f"""
# #             <div class="wire-src" data-wire="right-{i}">
# #               <div class="bigbtn">
# #                 <button class="edu-btn" onclick="window.location.hash='{i}'">
# #                   {m}
# #                 </button>
# #               </div>
# #             </div>
# #             """,
# #             unsafe_allow_html=True
# #         )

# #     st.markdown("</div>", unsafe_allow_html=True)



# import streamlit as st

# from core.progression import start_session, save_progress
# from core.badges import update_badges

# # Liste des modules (ou importée depuis ailleurs)
# MODULES = [
#     "420-411 - Interfaces humain-machine ",
#     "420-413 - Développement d'applications pour entreprise",
#     "420-511 - Développement de jeux vidéo",
#     "420-512 - Développement d'applications mobiles",
#     "420-514 - Collecte et interprétation de données",
# ]


# def render_right_panel() -> None:
#     st.markdown('<div class="right-modules">', unsafe_allow_html=True)

#     for module_label in MODULES:
#         if st.button(
#             module_label,
#             key=f"module_btn_{module_label}",
#             use_container_width=True
#         ):
#             # ==============================
#             # ✅ PROGRESSION : DÉMARRER SESSION
#             # ==============================
#             start_session(st.session_state.progress, module_label)
#             update_badges(st.session_state.progress)
#             save_progress(st.session_state.progress, user_id="default")

#             # ==============================
#             # État UI existant (si tu l’avais)
#             # ==============================
#             st.session_state.selected_module = module_label

#             # Optionnel : rediriger automatiquement vers le parcours
#             st.query_params["tab"] = "parcours"

#             st.rerun()

#     st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st

MODULES_RIGHT = [
    "420-411 - Interfaces humain-machine",
    "420-413 - Développement d'applications pour entreprise",
    "420-511 - Développement de jeux vidéo",
    "420-512 - Développement d'applications mobiles",
    "420-514 - Collecte et interprétation de données",
]

def render_right_panel() -> None:
    st.session_state.setdefault("selected_module", None)

    st.markdown('<div class="right-modules">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="top-nav-card" role="button" tabindex="0"
            onclick="
            const u=new URL(window.parent.location.href);
            u.searchParams.set('tab','competence');
            window.parent.location.href=u.toString();
            "
            onkeydown="if(event.key==='Enter'||event.key===' '){this.click();}">
        <div class="top-nav-inner">
            <svg class="nav-ico" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3a9 9 0 1 0 9 9" />
            <path d="M12 7a5 5 0 1 0 5 5" />
            <path d="M12 11a1 1 0 1 0 1 1" />
            <path d="M22 2l-7 7" />
            <path d="M18 2h4v4" />
            </svg>
            <span class="nav-text">Développer une compétence</span>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

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


