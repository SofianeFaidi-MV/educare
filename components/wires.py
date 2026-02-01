import json
import streamlit.components.v1 as components


def render_wires(module_labels=None):
    """
    - Pins visibles sur la bigarea (gauche + droite)
    - Surbrillance du fil + pins au clic / hover sur un module
    - Compatible boutons HTML (button.edu-btn) et st.button
    """
    if module_labels is None:
        module_labels = []

    payload = json.dumps(module_labels, ensure_ascii=False)

    components.html(
        f"""
        <script>
        (function() {{

          const PROVIDED = {payload} || [];

          function norm(s) {{
            return (s || "").replace(/\\s+/g, " ").trim();
          }}

          function getDoc() {{
            if (window.parent && window.parent.document) return window.parent.document;
            return document;
          }}

          function ensureOverlay(doc) {{
            let root = doc.getElementById("educare-wires-root");
            if (!root) {{
              root = doc.createElement("div");
              root.id = "educare-wires-root";
              root.style.position = "fixed";
              root.style.inset = "0";
              root.style.pointerEvents = "none";
              root.style.zIndex = "9999";

              const svg = doc.createElementNS("http://www.w3.org/2000/svg", "svg");
              svg.setAttribute("id", "educare-wires-svg");
              svg.style.width = "100%";
              svg.style.height = "100%";
              svg.style.overflow = "visible";

              root.appendChild(svg);
              doc.body.appendChild(root);
            }}
            return doc.getElementById("educare-wires-svg");
          }}

          function getAllCandidateButtons(doc) {{
            const htmlBtns = Array.from(doc.querySelectorAll("button.edu-btn"));
            const stBtns = Array.from(doc.querySelectorAll('div[data-testid="stButton"] button'));
            return htmlBtns.concat(stBtns);
          }}

          function inferModulesFromDOM(doc) {{
            const scoped = Array.from(
              doc.querySelectorAll(".left-modules button, .right-modules button")
            );

            const src = scoped.length ? scoped : getAllCandidateButtons(doc);
            const texts = src
              .map(b => norm(b.innerText))
              .filter(t => t.length > 0);

            return Array.from(new Set(texts));
          }}

          function findModuleButtons(doc, modules) {{
            const all = getAllCandidateButtons(doc);
            const set = new Set(modules.map(norm));
            return all.filter(btn => set.has(norm(btn.innerText)));
          }}

          // ---- Active / Hover state ----
          function setActive(doc, label) {{
            doc.documentElement.dataset.educareActiveModule = norm(label);
          }}
          function getActive(doc) {{
            return norm(doc.documentElement.dataset.educareActiveModule || "");
          }}
          function setHover(doc, label) {{
            doc.documentElement.dataset.educareHoverModule = norm(label);
          }}
          function getHover(doc) {{
            return norm(doc.documentElement.dataset.educareHoverModule || "");
          }}

          function installClickHandlers(doc, modules) {{
            if (doc.documentElement.dataset.educareWiresClicks === "1") return;
            doc.documentElement.dataset.educareWiresClicks = "1";

            doc.addEventListener("click", function(e) {{
              const btn = e.target && e.target.closest ? e.target.closest("button") : null;
              if (!btn) return;
              const t = norm(btn.innerText);
              if (!t) return;
              for (let i = 0; i < modules.length; i++) {{
                if (norm(modules[i]) === t) {{
                  setActive(doc, t);
                  setTimeout(draw, 30);
                  break;
                }}
              }}
            }}, true);

            doc.addEventListener("mouseover", function(e) {{
              const btn = e.target && e.target.closest ? e.target.closest("button") : null;
              if (!btn) return;
              const t = norm(btn.innerText);
              if (!t) return;
              for (let i = 0; i < modules.length; i++) {{
                if (norm(modules[i]) === t) {{
                  setHover(doc, t);
                  setTimeout(draw, 10);
                  break;
                }}
              }}
            }}, true);

            doc.addEventListener("mouseout", function(e) {{
              const btn = e.target && e.target.closest ? e.target.closest("button") : null;
              if (!btn) return;
              setHover(doc, "");
              setTimeout(draw, 10);
            }}, true);
          }}

          // ---- SVG helpers ----
          function el(doc, name) {{
            return doc.createElementNS("http://www.w3.org/2000/svg", name);
          }}

          function yAt(top, bottom, i, n) {{
            return top + (i + 1) * ((bottom - top) / (n + 1));
          }}

          function drawWire(doc, svg, d, isActive) {{
            const glow = el(doc, "path");
            glow.setAttribute("d", d);
            glow.setAttribute("fill", "none");
            glow.setAttribute("stroke-linecap", "round");
            glow.setAttribute("stroke", isActive ? "rgba(255,255,255,0.22)" : "rgba(255,255,255,0.10)");
            glow.setAttribute("stroke-width", isActive ? "14" : "9");
            svg.appendChild(glow);

            const path = el(doc, "path");
            path.setAttribute("d", d);
            path.setAttribute("fill", "none");
            path.setAttribute("stroke-linecap", "round");
            path.setAttribute("stroke", isActive ? "rgba(255,255,255,0.80)" : "rgba(255,255,255,0.40)");
            path.setAttribute("stroke-width", isActive ? "3.2" : "2");
            svg.appendChild(path);
          }}

          function drawPin(doc, svg, x, y, isActive) {{
            const g = el(doc, "circle");
            g.setAttribute("cx", x);
            g.setAttribute("cy", y);
            g.setAttribute("r", isActive ? "9" : "7");
            g.setAttribute("fill", isActive ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.10)");
            svg.appendChild(g);

            const c = el(doc, "circle");
            c.setAttribute("cx", x);
            c.setAttribute("cy", y);
            c.setAttribute("r", isActive ? "4.2" : "3.4");
            c.setAttribute("fill", isActive ? "rgba(255,255,255,0.90)" : "rgba(255,255,255,0.55)");
            svg.appendChild(c);
          }}

          function drawDot(doc, svg, x, y, isActive) {{
            const dot = el(doc, "circle");
            dot.setAttribute("cx", x);
            dot.setAttribute("cy", y);
            dot.setAttribute("r", isActive ? "4.0" : "3.2");
            dot.setAttribute("fill", isActive ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.55)");
            svg.appendChild(dot);
          }}

          // ---- Main draw ----
          function draw() {{
            const doc = getDoc();
            const svg = ensureOverlay(doc);
            if (!svg) return;

            const target = doc.querySelector(".bigarea");
            if (!target) {{
              svg.innerHTML = "";
              return;
            }}

            const modules = (PROVIDED && PROVIDED.length) ? PROVIDED : inferModulesFromDOM(doc);
            installClickHandlers(doc, modules);

            const btns = findModuleButtons(doc, modules);
            svg.innerHTML = "";

            const t = target.getBoundingClientRect();
            const leftEdge  = t.left;
            const rightEdge = t.right;

            const top = t.top + 28;
            const bottom = t.bottom - 28;
            const centerX = t.left + t.width / 2;

            const leftBtns = [];
            const rightBtns = [];

            for (let i = 0; i < btns.length; i++) {{
              const r = btns[i].getBoundingClientRect();
              const cx = r.left + r.width / 2;
              if (cx < centerX) leftBtns.push(btns[i]);
              else rightBtns.push(btns[i]);
            }}

            const active = getActive(doc);
            const hover = getHover(doc);

            // pins alignés sur la bigarea (un pin par bouton)
            const leftPins = leftBtns.map(function(b, i) {{
              return {{
                label: norm(b.innerText),
                x: leftEdge,
                y: yAt(top, bottom, i, leftBtns.length),
                btn: b
              }};
            }});

            const rightPins = rightBtns.map(function(b, i) {{
              return {{
                label: norm(b.innerText),
                x: rightEdge,
                y: yAt(top, bottom, i, rightBtns.length),
                btn: b
              }};
            }});

            // draw pins
            leftPins.forEach(function(p) {{
              const on = p.label && (p.label === active || p.label === hover);
              drawPin(doc, svg, p.x, p.y, on);
            }});
            rightPins.forEach(function(p) {{
              const on = p.label && (p.label === active || p.label === hover);
              drawPin(doc, svg, p.x, p.y, on);
            }});

            function wireFromBtnToPin(btn, pin) {{
              const r = btn.getBoundingClientRect();
              const isLeftSide = (pin.x === leftEdge);

              // sortie bouton côté bigarea
              const x1 = isLeftSide ? r.right : r.left;
              const y1 = r.top + r.height / 2;

              // entrée pin (sur le bord de bigarea)
              const x2 = pin.x;
              const y2 = pin.y;

              const mid = (x1 + x2) / 2;

              // ✅ PAS de template literal => pas de “Expected expression”
              const d =
                "M " + x1 + " " + y1 +
                " C " + mid + " " + y1 + ", " +
                         mid + " " + y2 + ", " +
                         x2 + " " + y2;

              const label = pin.label;
              const on = label && (label === active || label === hover);

              drawWire(doc, svg, d, on);
              drawDot(doc, svg, x1, y1, on);
            }}

            leftPins.forEach(function(p) {{ wireFromBtnToPin(p.btn, p); }});
            rightPins.forEach(function(p) {{ wireFromBtnToPin(p.btn, p); }});
          }}

          function schedule() {{
            setTimeout(draw, 120);
          }}

          // init
          schedule();

          // resize/scroll
          if (window.parent) {{
            window.parent.addEventListener("resize", schedule);
            window.parent.addEventListener("scroll", schedule, true);
          }} else {{
            window.addEventListener("resize", schedule);
            window.addEventListener("scroll", schedule, true);
          }}

          // DOM changes (Streamlit reruns)
          const doc = getDoc();
          const obs = new MutationObserver(function() {{ schedule(); }});
          obs.observe(doc.body, {{ childList: true, subtree: true }});

          // fallback
          setInterval(draw, 1000);

        }})();
        </script>
        """,
        height=0,
    )
