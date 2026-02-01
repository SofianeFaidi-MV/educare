import streamlit as st

def render_bottom_nav() -> None:
    c1, c2, _, _, _ = st.columns([1.4, 1.0, 1.0, 1.0, 1.2], gap="large")

    with c1:
        st.markdown(
            """
            <div class="bigbtn2">
              <button class="nav-svg-btn" onclick="
                const u=new URL(window.parent.location.href);
                u.searchParams.set('tab','parcours');
                window.parent.location.href=u.toString();
              ">
                <svg class="nav-ico" viewBox="0 0 64 64" aria-hidden="true">
                  <!-- icône 'route' -->
                  <path d="M20 6h8v10h-8V6zm0 18h8v10h-8V24zm0 18h8v10h-8V42z"></path>
                  <path d="M34 10c12 0 20 7 20 18 0 8-4 14-11 18l-4-6c5-3 7-7 7-12 0-7-5-12-12-12H34v-6z"></path>
                  <path d="M10 54l14-8 6 10-20-2z"></path>
                </svg>
                <span class="nav-text">Choisir un parcours d’apprentissage</span>
              </button>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            """
            <div class="bigbtn">
              <button class="nav-svg-btn" onclick="
                const u=new URL(window.parent.location.href);
                u.searchParams.set('tab','competence');
                window.parent.location.href=u.toString();
              ">
                <svg class="nav-ico" viewBox="0 0 64 64" aria-hidden="true">
                  <!-- icône 'target/skill' -->
                  <circle cx="32" cy="32" r="20" fill="none" stroke-width="4"></circle>
                  <circle cx="32" cy="32" r="10" fill="none" stroke-width="4"></circle>
                  <path d="M42 22l12-12" fill="none" stroke-width="4" stroke-linecap="round"></path>
                  <path d="M46 10h8v8" fill="none" stroke-width="4" stroke-linecap="round"></path>
                </svg>
                <span class="nav-text">Développer une compétence</span>
              </button>
            </div>
            """,
            unsafe_allow_html=True
        )
