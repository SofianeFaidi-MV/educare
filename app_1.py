import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from pathlib import Path
from core.state import init_state
from components.sidebar import render_left_panel
from components.right_panel import render_right_panel
from components.chat_area import render_center_area
from components.bottom_nav import render_bottom_nav
from components.top_right_progress import render_top_right_progress
from core.progression import load_progress
from components.wires import render_wires
from pages import parcours, competence, ressources, suivi, progression

st.set_page_config(page_title="EduCare – Coach empathique", layout="wide")

# même liste que tes panneaux gauche/droite
MODULES = [
    "420-111 - Introduction à la programmation",
    "420-112 - Création de sites web",
    "420-210 - Programmation orientée-objet",    
    "420-211 - Applications Web",    
    "420-311 - Structures de données",

    "420-411 - Interfaces humain-machine ",
    "420-413 - Développement d'applications pour entreprise",
    "420-511 - Développement de jeux vidéo",
    "420-512 - Développement d'applications mobiles",
    "420-514 - Collecte et interprétation de données",
]

def load_image_as_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def inject_bot_dot_logo(logo_path: str = "static/educare_logo_02.png") -> None:
    try:
        logo64 = load_image_as_base64(logo_path)
    except FileNotFoundError:
        st.warning(f"Logo introuvable: {logo_path} (le point bleu restera affiché)")
        return

    st.markdown(f"""
    <style>
    :root {{
    --educareLogo: url("data:image/png;base64,{logo64}");
    }}

    .bot-dot {{
    width: 30px;              /* ⬅️ AVANT ~14px → maintenant plus visible */
    height: 30px;
    min-width: 20px;
    min-height: 20px;

    background: var(--educareLogo) center/cover no-repeat !important;
    background-color: transparent !important;
    border-radius: 50% !important;

    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }}
    </style>
    """, unsafe_allow_html=True)



def load_css() -> None:
    css_path = Path(__file__).parent / "styles" / "main.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        '<div class="footer">© 2025 EduCare – Coach empathique pour étudiants en TI. Tous droits réservés.</div>',
        unsafe_allow_html=True
    )


def render_selected_page() -> None:
    tab = st.session_state.bottom_tab
    if tab == "Choisir un parcours d’apprentissage":
        print("Disparaitre le texte du bas de page")
    elif tab == "Développer une compétence":
        competence.render()
    elif tab == "Ressources":
        ressources.render()
    elif tab == "Suivi":
        suivi.render()
    elif tab == "Votre progression":
        progression.render()


def inject_intro_bot():
    messages = st.session_state.get("chat_messages", [])
    payload = json.dumps(messages, ensure_ascii=False)

    components.html(
        f"""
        <script>
        (function () {{
          const doc = (window.parent && window.parent.document) ? window.parent.document : document;
          const host = doc.getElementById("intro-bot");
          if (!host) return;

          const messages = {payload};

          host.innerHTML = `
            <div class="bot-card">
              <div class="bot-head">
                <div class="bot-dot"></div>
                <div class="bot-title">EduCare</div>
              </div>
              <div class="bot-body" id="bot-body"></div>
              <div class="bot-hint">Astuce : sélectionne un cours, puis pose une question.</div>
            </div>
          `;

          const body = host.querySelector("#bot-body");

          // ✅ état DOM persistant : combien de messages déjà rendus
          const already = parseInt(host.dataset.renderedCount || "0", 10);

          function scrollBottom() {{
            body.scrollTop = body.scrollHeight;
          }}

          function typeText(el, text, done) {{
            el.textContent = "";
            let k = 0;
            const speed = 16; // vitesse de frappe
            const timer = setInterval(() => {{
              el.textContent = text.slice(0, k++);
              scrollBottom();
              if (k > text.length) {{
                clearInterval(timer);
                done && done();
              }}
            }}, speed);
          }}

          // ✅ si rerun: on ne vide pas et on ne retape pas tout
          if (already === 0) {{
            body.innerHTML = "";
          }}

          // ajoute seulement les nouveaux messages
          const newMessages = (messages || []).slice(already);

          // s’il n’y a rien de nouveau : juste scroll
          if (newMessages.length === 0) {{
            scrollBottom();
            return;
          }}

          // file d’animation (assistant = typing, user = instant)
          let i = 0;
          function loop() {{
            if (i >= newMessages.length) {{
              host.dataset.renderedCount = String(messages.length);
              scrollBottom();
              return;
            }}

            const m = newMessages[i++];
            const div = doc.createElement("div");
            div.className = (m.role === "user") ? "user-bubble" : "bot-bubble";
            body.appendChild(div);

            if (m.role === "user") {{
              div.textContent = m.text || "";
              scrollBottom();
              setTimeout(loop, 50);
            }} else {{
              // typing assistant
              typeText(div, (m.text || ""), () => setTimeout(loop, 220));
            }}
          }}

          loop();
        }})();
        </script>
        """,
        height=0
    )



def _fmt_seconds(s: int) -> str:
    s = int(s or 0)
    h = s // 3600
    m = (s % 3600) // 60
    if h > 0:
        return f"{h} h {m:02d} min"
    return f"{m} min"

def inject_progress_popup(progress: dict) -> None:
    # ---- sources ----
    time_by = progress.get("time_by_module", {}) or {}
    questions_by = progress.get("questions_by_module", {}) or {}
    badges = progress.get("badges", []) or []
    selected = progress.get("selected_module") or "Aucun cours sélectionné"

    # ---- objectifs (ajuste selon ton choix) ----
    TARGET_MIN_PER_COURSE = 60      # 60 min = 100%
    TARGET_Q_PER_COURSE = 10        # 10 questions = 100%

    # ---- construire les barres par cours ----
    rows = []
    for module, sec in sorted(time_by.items(), key=lambda kv: int(kv[1] or 0), reverse=True):
        mins = int(sec or 0) // 60
        q = int(questions_by.get(module, 0) or 0)

        pct_time = min(100, int((mins / TARGET_MIN_PER_COURSE) * 100)) if TARGET_MIN_PER_COURSE else 0
        pct_q = min(100, int((q / TARGET_Q_PER_COURSE) * 100)) if TARGET_Q_PER_COURSE else 0

        # score combiné (50% temps, 50% questions)
        pct = int((pct_time * 0.5) + (pct_q * 0.5))

        rows.append({
            "module": module,
            "time": _fmt_seconds(sec),
            "questions": q,
            "pct": pct,
        })

    total_seconds = sum(int(v or 0) for v in time_by.values())
    total_questions = sum(int(v or 0) for v in questions_by.values())

    payload = {
        "selected_module": selected,
        "total_time": _fmt_seconds(total_seconds),
        "total_questions": total_questions,
        "courses": rows[:8],          # top 8 cours affichés
        "badges": badges,
    }

    components.html(
        """
        <script>
        (function() {
          const doc = (window.parent && window.parent.document) ? window.parent.document : document;
          const data = __PAYLOAD__;

          function closeModal() {
            const overlay = doc.getElementById("educare-progress-overlay");
            if (overlay) overlay.remove();
          }

          function openModal() {
            closeModal();

            const overlay = doc.createElement("div");
            overlay.id = "educare-progress-overlay";
            overlay.className = "educare-modal-overlay";

            const modal = doc.createElement("div");
            modal.className = "educare-modal";

            const badgeHtml = (data.badges || []).length
              ? (data.badges || []).map(b => `<span class="educare-badge">🏅 ${b}</span>`).join("")
              : `<div class="educare-empty">Aucun badge pour l’instant.</div>`;

            const courseHtml = (data.courses || []).length
              ? (data.courses || []).map(row => `
                  <div class="educare-course">
                    <div class="educare-course-top">
                      <div class="educare-course-name">${row.module}</div>
                      <div class="educare-course-meta">${row.time} · ${row.questions} q</div>
                    </div>
                    <div class="educare-bar">
                      <div class="educare-bar-fill" style="width:${row.pct}%"></div>
                    </div>
                    <div class="educare-course-foot">${row.pct}%</div>
                  </div>
                `).join("")
              : `<div class="educare-empty">Pas encore de données par cours.</div>`;

            modal.innerHTML = `
              <div class="educare-modal-head">
                <div class="educare-modal-title">Votre progression</div>
                <button class="educare-modal-x" aria-label="Fermer">×</button>
              </div>

              <div class="educare-modal-body">
                <div class="educare-metric">
                  <div class="educare-metric-k">Cours sélectionné</div>
                  <div class="educare-metric-v">${data.selected_module}</div>
                </div>

                <div class="educare-metric-grid">
                  <div class="educare-metric">
                    <div class="educare-metric-k">Temps total</div>
                    <div class="educare-metric-v">${data.total_time}</div>
                  </div>
                  <div class="educare-metric">
                    <div class="educare-metric-k">Questions posées</div>
                    <div class="educare-metric-v">${data.total_questions}</div>
                  </div>
                </div>

                <div class="educare-section-title">Badges</div>
                <div class="educare-badges">${badgeHtml}</div>

                <div class="educare-section-title">Progression par cours</div>
                <div class="educare-courses">
                  ${courseHtml}
                </div>

                <div class="educare-actions">
                  <button class="educare-secondary" id="educare-open-page">Ouvrir la page Progression</button>
                  <button class="educare-primary" id="educare-close">OK</button>
                </div>
              </div>
            `;

            overlay.appendChild(modal);
            doc.body.appendChild(overlay);

            overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });
            modal.querySelector(".educare-modal-x").addEventListener("click", closeModal);
            modal.querySelector("#educare-close").addEventListener("click", closeModal);

            modal.querySelector("#educare-open-page").addEventListener("click", () => {
              const u = new URL(window.parent.location.href);
              u.searchParams.set('tab','progression');
              window.parent.location.href = u.toString();
            });

            function onKey(e) {
              if (e.key === "Escape") {
                closeModal();
                doc.removeEventListener("keydown", onKey);
              }
            }
            doc.addEventListener("keydown", onKey);
          }

          const btn = doc.querySelector(".progression-svg-btn");
          if (!btn) return;

          if (btn.dataset.progressBound === "1") return;
          btn.dataset.progressBound = "1";

          btn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            openModal();
          }, true);
        })();
        </script>
        """.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False)),
        height=0
    )
    
def inject_blinking_underscore():
    components.html(
        """
        <script>
        (function () {
          const doc = (window.parent && window.parent.document) ? window.parent.document : document;

          // ✅ cible Streamlit (stable)
          const ta = doc.querySelector('div[data-testid="stTextArea"] textarea');
          if (!ta) return;

          const wrap = ta.parentElement; // ✅ wrapper direct du textarea (meilleur pour top/left)
          if (!wrap) return;

          wrap.style.position = "relative";

          // caret
          let caret = doc.getElementById("educare-caret-auto");
          if (!caret) {
            caret = doc.createElement("span");
            caret.id = "educare-caret-auto";
            caret.textContent = "_";
            caret.style.position = "absolute";
            caret.style.pointerEvents = "none";
            caret.style.zIndex = "999999";
            caret.style.fontWeight = "800";
            caret.style.color = "rgba(255,255,255,0.85)";
            wrap.appendChild(caret);
            caret.textContent = "_";
            caret.style.fontWeight = "900";
            caret.style.fontSize = "1.05em";
            caret.style.transform = "translateY(8px)";  // ⬅️ le remonte visuellement

          }

          function measureTextWidth(text, font) {
            const canvas = measureTextWidth._c || (measureTextWidth._c = doc.createElement("canvas"));
            const ctx = canvas.getContext("2d");
            ctx.font = font;
            return ctx.measureText(text).width;
          }

          function positionCaret() {
            const empty = (ta.value.trim().length === 0);
            caret.style.display = empty ? "inline-block" : "none";
            if (!empty) return;

            const cs = window.getComputedStyle(ta);
            const placeholder = ta.getAttribute("placeholder") || "";
            const font = `${cs.fontStyle} ${cs.fontVariant} ${cs.fontWeight} ${cs.fontSize} / ${cs.lineHeight} ${cs.fontFamily}`;
            const padL = parseFloat(cs.paddingLeft) || 0;
            const padT = parseFloat(cs.paddingTop) || 0;

            const textW = measureTextWidth(placeholder, font);

            caret.style.left = (padL + textW + 4) + "px";
            ccaret.style.top  = (padT + 8) + "px";  // ✅ descend

          }

          // ✅ blink garanti (visibility + RAF)
          if (!caret.dataset.rafBlink) {
            caret.dataset.rafBlink = "1";
            let last = 0;
            let visible = true;

            function tick(t) {
              const shown = (caret.style.display !== "none");

              if (shown && (t - last > 520)) {
                visible = !visible;
                caret.style.setProperty("visibility", visible ? "visible" : "hidden", "important");
                last = t;
              }

              if (!shown) {
                caret.style.setProperty("visibility", "visible", "important");
                visible = true;
                last = t;
              }

              requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
          }

          ta.addEventListener("input", positionCaret);
          ta.addEventListener("focus", () => {
  // cacher le caret custom
  caret.style.display = "none";

  // cacher l'icône 💬 si présente
  const icon = ta.closest(".chatbox")?.querySelector(".chat-icon");
  if (icon) icon.style.display = "none";
});
          ta.addEventListener("blur", positionCaret);
          window.addEventListener("resize", positionCaret);

          positionCaret();
        })();
        </script>
        """,
        height=0
    )




def inject_js_debug_counter():
    components.html(
        """
        <script>
        (function () {
          const doc = (window.parent && window.parent.document) ? window.parent.document : document;

          // évite double injection
          if (doc.getElementById("educare-debug-counter")) return;

          const box = doc.createElement("div");
          box.id = "educare-debug-counter";
          box.style.position = "fixed";
          box.style.bottom = "20px";
          box.style.right = "20px";
          box.style.zIndex = "999999";
          box.style.padding = "8px 12px";
          box.style.borderRadius = "10px";
          box.style.fontFamily = "monospace";
          box.style.fontSize = "14px";
          box.style.background = "rgba(0,0,0,0.7)";
          box.style.color = "#00ff9c";
          box.textContent = "JS tick: 0";

          doc.body.appendChild(box);

          let i = 0;
          function tick() {
            i++;
            box.textContent = "JS tick: " + i;
            requestAnimationFrame(tick);
          }
          requestAnimationFrame(tick);
        })();
        </script>
        """,
        height=0
    )




def main() -> None:
    init_state()

    st.session_state.setdefault("selected_module", None)

      # ✅ lire tab depuis l’URL (query params)
    
        # ✅ PROGRESSION: init obligatoire avant tout render
    if "progress" not in st.session_state:
        st.session_state.progress = load_progress(user_id="default")
        
    tab = st.query_params.get("tab")
    if tab in {"parcours", "competence", "ressources", "suivi", "progression"}:
        st.session_state.bottom_tab = tab

    load_css()
    inject_bot_dot_logo("static/educare_logo_02.png")


    # ✅ 1) Colonnes principales
    left, center, right = st.columns([1.15, 2.8, 1.15], gap="large")

    with left:
        render_left_panel()

    with center:
        render_center_area()
        # inject_js_debug_counter() 
        inject_blinking_underscore()
        inject_intro_bot()
        render_selected_page()


    # with right:
    #     render_right_panel()

    with right:
        st.markdown('<div class="right-col-wrap">', unsafe_allow_html=True)

        render_top_right_progress()               # 1️⃣ le bouton
        inject_progress_popup(st.session_state.progress)  # 2️⃣ le popup
        render_right_panel()                      # 3️⃣ le reste
        st.markdown('</div>', unsafe_allow_html=True)


    # 2) Nav du bas
    # render_bottom_nav()

    # 3) Wires (APRÈS que tout soit rendu : boutons + bigarea)
    render_wires(MODULES)

    # 4) Footer
    render_footer()


if __name__ == "__main__":
    main()
