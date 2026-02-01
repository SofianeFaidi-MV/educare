import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from pathlib import Path
import time
from core.state import init_state
from components.sidebar import render_left_panel
from components.right_panel import render_right_panel
from components.chat_area import render_center_area
from components.top_right_progress import render_top_right_progress
from core.progression import load_progress
from components.wires import render_wires
from pages import competence, ressources, suivi, progression
from core.progression import save_progress
from core.progression import save_progress, log_question
from core.badges import update_badges



# ✅ UNE SEULE FOIS
st.set_page_config(page_title="EduCare – Coach empathique", layout="wide")

# même liste que tes panneaux gauche/droite
MODULES = [
    "420-111 - Introduction à la programmation",
    "420-112 - Création de sites web",
    "420-210 - Programmation orientée-objet",
    "420-211 - Applications Web",
    "420-311 - Structures de données",
    "420-411 - Interfaces humain-machine",
    "420-413 - Développement d'applications pour entreprise",
    "420-511 - Développement de jeux vidéo",
    "420-512 - Développement d'applications mobiles",
    "420-514 - Collecte et interprétation de données",
]


# -------------------------
# Helpers / init UI
# -------------------------
def load_image_as_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inject_bot_dot_logo(logo_path: str = "static/educare_logo_02.png") -> None:
    try:
        logo64 = load_image_as_base64(logo_path)
    except FileNotFoundError:
        st.warning(f"Logo introuvable: {logo_path} (le point bleu restera affiché)")
        return

    st.markdown(
        f"""
        <style>
        :root {{
          --educareLogo: url("data:image/png;base64,{logo64}");
        }}
        .bot-dot {{
          width: 30px;
          height: 30px;
          min-width: 20px;
          min-height: 20px;
          background: var(--educareLogo) center/cover no-repeat !important;
          background-color: transparent !important;
          border-radius: 50% !important;
          box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_css() -> None:
    css_path = Path(__file__).parent / "styles" / "main.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        '<div class="footer">© 2025 EduCare – Coach empathique pour étudiants en TI. Tous droits réservés.</div>',
        unsafe_allow_html=True,
    )


def render_selected_page() -> None:
    tab = st.session_state.get("bottom_tab", "Choisir un parcours d’apprentissage")

    if tab == "Choisir un parcours d’apprentissage":
        # (si tu veux vraiment rien afficher ici)
        return
    elif tab == "Développer une compétence":
        competence.render()
    elif tab == "Ressources":
        ressources.render()
    elif tab == "Suivi":
        suivi.render()
    elif tab == "Votre progression":
        progression.render()

def inject_intro_bot():
    if st.session_state.get("request_learning_path"):
        st.session_state["request_learning_path"] = False

        selected = st.session_state.get("selected_module")
        if not selected:
            st.session_state["chat_messages"].append({
                "role": "assistant",
                "text": "👈 Choisis d’abord un cours, puis clique sur « Choisir un parcours d’apprentissage »."
            })
        else:
            # 1) message user
            st.session_state["chat_messages"].append({
                "role": "user",
                "text": "Je veux un parcours d’apprentissage pour ce cours."
            })

            # 2) message coach (RAG)
            from core.coach import generate_reply
            reply = generate_reply(
                "Propose-moi une séquence d’apprentissage structurée (étapes 1..N) pour ce cours.",
                context={"module": selected}
            )
            st.session_state["chat_messages"].append({"role": "assistant", "text": reply})

        st.rerun()


    messages = st.session_state.get("chat_messages", [])
    payload = json.dumps(messages, ensure_ascii=False)

    components.html(
        f"""
<script>
(function () {{
  try {{
    var doc = (window.parent && window.parent.document) ? window.parent.document : document;
    var host = doc.getElementById("intro-bot");
    if (!host) return;

    var messages = {payload};

    var W = window.parent || window;
    W.__educareChat = W.__educareChat || {{
      lastAnimatedKey: null,
      wordTimer: null
    }};

    function cleanup() {{
      if (W.__educareChat.wordTimer) {{
        clearInterval(W.__educareChat.wordTimer);
        W.__educareChat.wordTimer = null;
      }}
    }}

    function ensureUI() {{
      if (host.querySelector(".bot-card")) return;
      host.innerHTML =
        '<div class="bot-card">' +
          '<div class="bot-head">' +
            '<div class="bot-dot"></div>' +
            '<div class="bot-title">EduCare</div>' +
          '</div>' +
          '<div class="bot-body" id="bot-body"></div>' +
          '<div class="bot-hint">Astuce : sélectionne un cours, puis pose une question.</div>' +
        '</div>';
    }}

    function scrollBottom() {{
      var body = host.querySelector("#bot-body");
      if (!body) return;
      body.scrollTop = body.scrollHeight;
    }}

    function addBubble(role, text) {{
      var body = host.querySelector("#bot-body");
      if (!body) return null;
      var div = doc.createElement("div");
      div.className = (role === "user") ? "user-bubble" : "bot-bubble";
      div.textContent = (text !== undefined && text !== null) ? String(text) : "";
      body.appendChild(div);
      return div;
    }}

    // ✅ typing mot par mot (stable)
    function typeWords(el, fullText, done) {{
      cleanup();
      fullText = (fullText !== undefined && fullText !== null) ? String(fullText) : "";
      el.textContent = "";

      // split en mots en gardant les espaces
      var parts = fullText.split(/(\\s+)/);

      // ⚙️ vitesse (change ici)
      var WORDS_PER_SEC = 10; // ⬅️ plus petit = plus lent
      var STEP_MS = Math.max(90, Math.floor(1000 / WORDS_PER_SEC));

      var i = 0;
      var out = "";

      W.__educareChat.wordTimer = setInterval(function() {{
        if (i < parts.length) {{
          out += parts[i++];
          el.textContent = out;
          scrollBottom();
          return;
        }}
        cleanup();
        if (done) done();
      }}, STEP_MS);
    }}

    // ---------------------------
    // 1) Construire UI + reset body
    // ---------------------------
    ensureUI();
    var body = host.querySelector("#bot-body");
    if (!body) return;

    // IMPORTANT: on reconstruit tout à chaque rerun (anti-duplication total)
    cleanup();
    body.innerHTML = "";

    // ---------------------------
    // 2) Trouver le dernier message assistant à animer
    // ---------------------------
    var lastAssistantIndex = -1;
    for (var k = messages.length - 1; k >= 0; k--) {{
      if (messages[k] && messages[k].role === "assistant") {{
        lastAssistantIndex = k;
        break;
      }}
    }}

    // clé unique pour savoir si on a déjà animé ce dernier message
    var lastKey = null;
    if (lastAssistantIndex >= 0) {{
      var t = (messages[lastAssistantIndex].text !== undefined && messages[lastAssistantIndex].text !== null)
        ? String(messages[lastAssistantIndex].text)
        : "";
      lastKey = String(lastAssistantIndex) + "::" + String(t.length);
    }}

    // ---------------------------
    // 3) Render tout: instant sauf le dernier assistant (si nouveau)
    // ---------------------------
    for (var i = 0; i < messages.length; i++) {{
      var m = messages[i] || {{}};
      var role = m.role || "assistant";
      var txt = (m.text !== undefined && m.text !== null) ? String(m.text) : "";

      var bubble = addBubble(role, txt);

      // animer seulement le dernier assistant, une seule fois
      if (i === lastAssistantIndex && role === "assistant" && lastKey && W.__educareChat.lastAnimatedKey !== lastKey) {{
        // remplace le contenu par typing
        typeWords(bubble, txt, function() {{
          W.__educareChat.lastAnimatedKey = lastKey;
          scrollBottom();
        }});
      }}
    }}

    scrollBottom();

    // si rien à animer, on garde la clé en sync
    if (lastKey && W.__educareChat.lastAnimatedKey !== lastKey) {{
      // on ne force pas l'anim si déjà affiché instant au-dessus
      // mais on sync la clé pour éviter anim répétée
      W.__educareChat.lastAnimatedKey = lastKey;
    }}

  }} catch (e) {{
    console.error("inject_intro_bot error:", e);
  }}
}})();
</script>
        """,
        height=0,
    )




# -------------------------
# Progress popup helpers
# -------------------------
def _fmt_seconds(s: int) -> str:
    s = int(s or 0)
    h = s // 3600
    m = (s % 3600) // 60
    if h > 0:
        return f"{h} h {m:02d} min"
    return f"{m} min"


def inject_progress_popup(progress: dict) -> None:
    time_by = progress.get("time_by_module_sec", {}) or {}
    questions_by = progress.get("questions_by_module", {}) or {}
    badges = progress.get("badges", []) or []

    selected_ui = st.session_state.get("selected_module")
    selected = selected_ui or progress.get("selected_module") or "Aucun cours sélectionné"

    TARGET_MIN_PER_COURSE = 60
    TARGET_Q_PER_COURSE = 10

    rows = []
    for module, sec in sorted(time_by.items(), key=lambda kv: int(kv[1] or 0), reverse=True):
        mins = int(sec or 0) // 60
        q = int(questions_by.get(module, 0) or 0)

        pct_time = min(100, int((mins / TARGET_MIN_PER_COURSE) * 100)) if TARGET_MIN_PER_COURSE else 0
        pct_q = min(100, int((q / TARGET_Q_PER_COURSE) * 100)) if TARGET_Q_PER_COURSE else 0
        pct = int((pct_time * 0.5) + (pct_q * 0.5))

        rows.append({"module": module, "time": _fmt_seconds(sec), "questions": q, "pct": pct})

    total_seconds = sum(int(v or 0) for v in time_by.values())
    total_questions = sum(int(v or 0) for v in questions_by.values())

    payload = {
        "selected_module": selected,
        "total_time": _fmt_seconds(total_seconds),
        "total_questions": total_questions,
        "courses": rows[:8],
        "badges": badges,
    }

    components.html(
        f"""
        <script>
        (function() {{
          const doc = (window.parent && window.parent.document) ? window.parent.document : document;
          const W = window.parent || window;

          // ✅ 1) payload TOUJOURS à jour (rerun Streamlit)
          W.__educareProgressPayload = {json.dumps(payload, ensure_ascii=False)};

          function closeModal() {{
            const overlay = doc.getElementById("educare-progress-overlay");
            if (overlay) overlay.remove();
          }}

          function openModal() {{
            closeModal();

            // ✅ 2) on lit le payload LIVE au moment du click
            const data = W.__educareProgressPayload || {{}};

            const overlay = doc.createElement("div");
            overlay.id = "educare-progress-overlay";
            overlay.className = "educare-modal-overlay";

            const modal = doc.createElement("div");
            modal.className = "educare-modal";

            const badgeHtml = (data.badges || []).length
              ? (data.badges || []).map(b => `<span class="educare-badge">🏅 ${{b}}</span>`).join("")
              : `<div class="educare-empty">Aucun badge pour l’instant.</div>`;

            const courseHtml = (data.courses || []).length
              ? (data.courses || []).map(row => `
                  <div class="educare-course">
                    <div class="educare-course-top">
                      <div class="educare-course-name">${{row.module}}</div>
                      <div class="educare-course-meta">${{row.time}} · ${{row.questions}} q</div>
                    </div>
                    <div class="educare-bar">
                      <div class="educare-bar-fill" style="width:${{row.pct}}%"></div>
                    </div>
                    <div class="educare-course-foot">${{row.pct}}%</div>
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
                  <div class="educare-metric-v">${{data.selected_module || "Aucun cours sélectionné"}}</div>
                </div>

                <div class="educare-metric-grid">
                  <div class="educare-metric">
                    <div class="educare-metric-k">Temps total</div>
                    <div class="educare-metric-v">${{data.total_time || "0 min"}}</div>
                  </div>
                  <div class="educare-metric">
                    <div class="educare-metric-k">Questions posées</div>
                    <div class="educare-metric-v">${{data.total_questions ?? 0}}</div>
                  </div>
                </div>

                <div class="educare-section-title">Badges</div>
                <div class="educare-badges">${{badgeHtml}}</div>

                <div class="educare-section-title">Progression par cours</div>
                <div class="educare-courses">${{courseHtml}}</div>

                <div class="educare-actions">
                  <button class="educare-secondary" id="educare-open-page">Ouvrir la page Progression</button>
                  <button class="educare-primary" id="educare-close">OK</button>
                </div>
              </div>
            `;

            overlay.appendChild(modal);
            doc.body.appendChild(overlay);

            overlay.addEventListener("click", (e) => {{ if (e.target === overlay) closeModal(); }});
            modal.querySelector(".educare-modal-x").addEventListener("click", closeModal);
            modal.querySelector("#educare-close").addEventListener("click", closeModal);

            modal.querySelector("#educare-open-page").addEventListener("click", () => {{
              const u = new URL(window.parent.location.href);
              u.searchParams.set('tab','progression');
              window.parent.location.href = u.toString();
            }});

            function onKey(e) {{
              if (e.key === "Escape") {{
                closeModal();
                doc.removeEventListener("keydown", onKey);
              }}
            }}
            doc.addEventListener("keydown", onKey);
          }}

          const btn = doc.querySelector(".progression-svg-btn");
          if (!btn) return;

          // ✅ 3) un seul bind, MAIS payload live
          if (btn.dataset.progressBound === "1") return;
          btn.dataset.progressBound = "1";

          btn.addEventListener("click", (e) => {{
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            openModal();
          }}, true);
        }})();
        </script>
        """,
        height=0,
    )



def inject_blinking_underscore():
    components.html(
        """
        <script>
        (function () {
          const doc = (window.parent && window.parent.document) ? window.parent.document : document;
          const ta = doc.querySelector('div[data-testid="stTextArea"] textarea');
          if (!ta) return;

          const wrap = ta.parentElement;
          if (!wrap) return;
          wrap.style.position = "relative";

          let caret = doc.getElementById("educare-caret-auto");
          if (!caret) {
            caret = doc.createElement("span");
            caret.id = "educare-caret-auto";
            caret.textContent = "_";
            caret.style.position = "absolute";
            caret.style.pointerEvents = "none";
            caret.style.zIndex = "999999";
            caret.style.fontWeight = "900";
            caret.style.color = "rgba(255,255,255,0.85)";
            caret.style.fontSize = "1.05em";
            caret.style.transform = "translateY(8px)";
            wrap.appendChild(caret);
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
            caret.style.top  = (padT + 8) + "px";
          }

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
          ta.addEventListener("focus", () => { caret.style.display = "none"; });
          ta.addEventListener("blur", positionCaret);
          window.addEventListener("resize", positionCaret);

          positionCaret();
        })();
        </script>
        """,
        height=0,
    )


# -------------------------
# Session logic
# -------------------------
def ensure_session_defaults():
    st.session_state.setdefault("module_entered_at", None)
    st.session_state.setdefault("module_timer_start", None)

    st.session_state.setdefault("selected_module", None)
    st.session_state.setdefault("last_selected_module", None)
    st.session_state.setdefault("bottom_tab", "Choisir un parcours d’apprentissage")

    st.session_state.setdefault("chat_input_main", "")
    st.session_state.setdefault("chat_input", "")

    # ✅ token utilisé par inject_intro_bot (JS)
    st.session_state.setdefault("chat_reset_token", 0)

    st.session_state.setdefault("chat_messages", [
        {"role": "assistant", "text": "Salut 👋 Je suis EduCare, ton coach d’apprentissage."},
        {"role": "assistant", "text": "1) Commence par choisir un cours à gauche ou à droite."},
        {"role": "assistant", "text": "2) Ensuite, écris ta question dans la zone de chat."},
        {"role": "assistant", "text": "Exemples : « Explique-moi les boucles » ou « Donne-moi un exercice sur les listes »."},
    ])



def on_module_change_reset_chat():
    now = time.time()
    prev = st.session_state.get("last_selected_module")
    current = st.session_state.get("selected_module")

    progress = st.session_state.get("progress")

        # ⏱️ arrêter le chrono de l'ancien module
    if prev and progress and st.session_state.get("module_timer_start"):
        elapsed = int(now - st.session_state["module_timer_start"])
        t_by = progress.setdefault("time_by_module_sec", {})
        t_by[prev] = int(t_by.get(prev, 0)) + elapsed
        save_progress(progress, user_id="default")

    # ⏱️ démarrer le chrono du nouveau module
    if current:
        st.session_state["module_timer_start"] = now
    else:
        st.session_state["module_timer_start"] = None

    # 1) sauver le temps du module précédent
    entered_at = st.session_state.get("module_entered_at")
    if progress and prev and entered_at:
        elapsed = int(now - entered_at)
        t = progress.setdefault("time_by_module_sec", {})
        t[prev] = int(t.get(prev, 0)) + max(0, elapsed)
        save_progress(progress, user_id="default")

    # 2) démarrer le chrono du nouveau module
    st.session_state["module_entered_at"] = now
    selected = st.session_state.get("selected_module")

    if selected != st.session_state.get("last_selected_module"):
        st.session_state["last_selected_module"] = selected

        # 🔥 déclenche le reset JS du chat (inject_intro_bot lit ça)
        st.session_state["chat_reset_token"] += 1

        # (optionnel mais propre)
        st.session_state["chat_input_main"] = ""
        st.session_state["chat_input"] = ""

        if selected:
            st.session_state["chat_messages"] = [
                {"role": "assistant", "text": f"✅ Module sélectionné : {selected}."},
                {"role": "assistant", "text": "Pose ta question dans la zone de chat, et je te réponds."},
            ]
        else:
            st.session_state["chat_messages"] = [
                {"role": "assistant", "text": "Salut 👋 Je suis EduCare, ton coach d’apprentissage."},
                {"role": "assistant", "text": "1) Commence par choisir un cours à gauche ou à droite."},
                {"role": "assistant", "text": "2) Ensuite, écris ta question dans la zone de chat."},
                {"role": "assistant", "text": "Exemples : « Explique-moi les boucles » ou « Donne-moi un exercice sur les listes »."},
            ]


def sync_tab_from_url():
    tab = st.query_params.get("tab")
    mapping = {
        "parcours": "Choisir un parcours d’apprentissage",
        "competence": "Développer une compétence",
        "ressources": "Ressources",
        "suivi": "Suivi",
        "progression": "Votre progression",
    }
    if tab in mapping:
        st.session_state["bottom_tab"] = mapping[tab]


def main() -> None:
    init_state()
    ensure_session_defaults()
    sync_tab_from_url()
    on_module_change_reset_chat()
    

    # ✅ progression init (hors du if module-change)
    if "progress" not in st.session_state:
        st.session_state["progress"] = load_progress(user_id="default")

    load_css()
    inject_bot_dot_logo("static/educare_logo_02.png")

    left, center, right = st.columns([1.15, 2.8, 1.15], gap="large")

    with left:
        clicked_path = render_left_panel()

        # ✅ si clic -> on déclenche une requête "parcours" et on rerun
        if clicked_path:
            st.session_state["request_learning_path"] = True
            st.rerun()


    with center:
        render_center_area()
        inject_blinking_underscore()
        inject_intro_bot()
        render_selected_page()

    with right:
        st.markdown('<div class="right-col-wrap">', unsafe_allow_html=True)
        render_top_right_progress()
        inject_progress_popup(st.session_state["progress"])
        render_right_panel()
        st.markdown("</div>", unsafe_allow_html=True)

    render_wires(MODULES)
    render_footer()


if __name__ == "__main__":
    main()