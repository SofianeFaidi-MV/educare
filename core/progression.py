import json
import time
from pathlib import Path
from core.competences_map import MODULE_TO_COMP

DATA_PATH = Path("data") / "progression.json"


def _now() -> float:
    return time.time()

def get_module_progress_pct(progress: dict, module: str) -> int:
    TARGET_MIN = 60     # 60 min = 100 %
    TARGET_Q = 10       # 10 questions = 100 %

    sec = int(progress.get("time_by_module", {}).get(module, 0))
    q = int(progress.get("questions_by_module", {}).get(module, 0))

    pct_time = min(100, (sec / 60) / TARGET_MIN * 100) if TARGET_MIN else 0
    pct_q = min(100, q / TARGET_Q * 100) if TARGET_Q else 0

    return int(0.5 * pct_time + 0.5 * pct_q)

def load_progress(user_id: str = "default") -> dict:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        db = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    else:
        db = {}

    if user_id not in db:
        db[user_id] = {
            "selected_module": None,
            "active_session": {"start_ts": None, "module": None},
            "time_by_module_sec": {},         # {"420-111 ...": 1234}
            "questions_by_module": {},        # {"420-111 ...": 7}
            "competences": {},                # {"Algo": 0.35, "Web": 0.12}
            "badges": [],                     # ["Premier pas", ...]
            "events": [],                     # journal (optionnel)
        }
        DATA_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    return db[user_id]


def save_progress(state: dict, user_id: str = "default") -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        db = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    else:
        db = {}
    db[user_id] = state
    DATA_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def start_session(state: dict, module_label: str) -> None:
    # clôture session précédente si besoin
    stop_session(state)
    state["selected_module"] = module_label
    state["active_session"] = {"start_ts": _now(), "module": module_label}
    state["events"].append({"ts": _now(), "type": "select_module", "module": module_label})


def stop_session(state: dict) -> None:
    sess = state.get("active_session") or {}
    start_ts = sess.get("start_ts")
    module = sess.get("module")
    if start_ts and module:
        dt = max(0, _now() - start_ts)
        state["time_by_module_sec"][module] = state["time_by_module_sec"].get(module, 0) + dt
    state["active_session"] = {"start_ts": None, "module": None}


def log_question(state: dict, module_label: str) -> None:
    state["questions_by_module"][module_label] = state["questions_by_module"].get(module_label, 0) + 1
    state["events"].append({"ts": _now(), "type": "question", "module": module_label})

def update_competences(state: dict, module_label: str, delta: float = 0.05) -> None:
    """
    Incrémente les compétences associées à un module.
    """
    if not module_label:
        return

    tags = MODULE_TO_COMP.get(module_label, [])
    if not tags:
        return

    competences = state.setdefault("competences", {})

    for tag in tags:
        key = tag.lower()
        competences[key] = min(1.0, competences.get(key, 0.0) + delta)