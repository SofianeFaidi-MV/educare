def update_competences(state: dict, module_label: str, delta: float = 0.05, module_to_comp=None) -> None:
    if not module_to_comp:
        return
    for c in module_to_comp.get(module_label, []):
        state["competences"][c] = min(1.0, state["competences"].get(c, 0.0) + delta)


def update_badges(state: dict) -> None:
    badges = set(state.get("badges", []))

    total_questions = sum(state.get("questions_by_module", {}).values())
    total_time = sum(state.get("time_by_module_sec", {}).values())

    if total_questions >= 1:
        badges.add("Premier pas")
    if total_questions >= 10:
        badges.add("Curieux")
    if total_time >= 30 * 60:
        badges.add("30 minutes")
    if len(state.get("time_by_module_sec", {})) >= 3:
        badges.add("Explorateur")

    state["badges"] = sorted(badges)
