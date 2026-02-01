import streamlit as st

# def render_top_right_progress() -> None:
#     st.markdown(
#         """
#         <div class="top-progress-btn">
#           <button class="progression-svg-btn" onclick="
#             const u = new URL(window.parent.location.href);
#             u.searchParams.set('tab','progression');
#             window.parent.location.href = u.toString();
#           ">
#             <svg class="prog-ico" viewBox="0 0 64 64" aria-hidden="true">
#               <!-- icône 'graph' (exemple). Tu peux remplacer par TON SVG -->
#               <rect x="8"  y="34" width="8" height="22" rx="2"></rect>
#               <rect x="22" y="26" width="8" height="30" rx="2"></rect>
#               <rect x="36" y="18" width="8" height="38" rx="2"></rect>
#               <path d="M10 18 L26 12 L40 16 L54 6" fill="none" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>
#               <path d="M54 6 L52 14 L60 10 Z"></path>
#             </svg>
#             <span class="prog-text">Votre progression</span>
#           </button>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )



def render_top_right_progress() -> None:
    st.markdown(
        """
        <div class="top-progress-btn">
          <button class="progression-svg-btn" onclick="
            const u = new URL(window.parent.location.href);
            u.searchParams.set('tab','progression');
            window.parent.location.href = u.toString();
          ">
            <svg class="prog-ico" viewBox="0 0 64 64" aria-hidden="true">
             <rect x="10" y="34" width="8" height="20" rx="3"></rect>
              <rect x="22" y="28" width="8" height="26" rx="3"></rect>
              <rect x="34" y="20" width="8" height="34" rx="3"></rect>
              <rect x="46" y="14" width="8" height="40" rx="3"></rect>
                <path d="M10 36 L26 26 L38 30 L50 18 L58 12"
        fill="none"
        stroke-width="5.5"
        stroke-linecap="round"
        stroke-linejoin="round"></path>
              <path d="M58 12 L50 12 L54 4 Z"></path>
            </svg>
            <span class="prog-text">Votre progression</span>
          </button>
        </div>
        """,
        unsafe_allow_html=True
    )
