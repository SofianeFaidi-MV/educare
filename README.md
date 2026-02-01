# EduCare (Streamlit)

Prototype UI Streamlit inspiré de ton mockup (3 colonnes + navigation bas).

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```




## Lancer l’app
```bash
streamlit run app.py
```

## Structure
- `components/` : UI (panneaux gauche/droite, chat, nav bas)
- `pages/` : contenus par section (placeholders)
- `core/` : logique métier (placeholders coach/reco/state)
- `styles/main.css` : style global

## Notes
- Ajoute ton logo dans `assets/logo.png` puis remplace le placeholder dans `components/sidebar.py`.
