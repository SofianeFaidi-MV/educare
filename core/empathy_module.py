# core/empathy_module.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple
import re


class EmpathyMode(str, Enum):
    NEUTRAL = "neutral"
    ENCOURAGE = "encourage"
    NORMALIZE_ERROR = "normalize_error"
    STEP_BY_STEP = "step_by_step"
    CLARIFY = "clarify"
    REDUCE_COGNITIVE_LOAD = "reduce_cognitive_load"


@dataclass
class EmpathySignal:
    """Signal explicite/contextuel détecté dans le message."""
    name: str
    weight: float
    evidence: str


@dataclass
class EmpathyDecision:
    """Décision empathique pour une requête."""
    mode: EmpathyMode
    intensity: float  # 0..1
    signals: List[EmpathySignal]


class EmpathyModule:
    """
    Module empathique pragmatique:
    - Détecte des signaux explicites de difficulté/confusion.
    - Déclenche une stratégie de réponse (mode + intensité).
    - Formate la réponse finale en gardant le contenu RAG.
    """

    # Expressions simples (à adapter à ton contexte/lexique étudiant)
    _PATTERNS: List[Tuple[str, float, str]] = [
        (r"\b(j(e|')? comprend(s)? pas|je ne comprends pas)\b", 0.9, "Expression de non-compréhension"),
        (r"\b(c'?est|cest) (trop )?(dur|difficile)\b", 0.8, "Difficulté déclarée"),
        (r"\b(j(e|')? suis bloqu(é|ee?)|bloqué|bloquee?)\b", 0.9, "Blocage déclaré"),
        (r"\b(aide|help|svp|s'il te plait|stp)\b", 0.4, "Demande d’aide"),
        (r"\b(exemple|un exemple)\b", 0.5, "Demande d’exemple"),
        (r"\b(pas[- ]?à[- ]?pas|étape par étape)\b", 0.7, "Demande pas-à-pas"),
        (r"\b(résume|résumé|plus simple|simplifie)\b", 0.6, "Demande de simplification"),
        (r"\b(j(e|')? suis stress(é|ee?)|anxieux|angoiss(é|ee?))\b", 0.9, "Stress déclaré"),
        (r"\b(encore|toujours)\b", 0.2, "Répétition (faible)"),
    ]

    def analyze(self, user_text: str) -> List[EmpathySignal]:
        text = user_text.lower().strip()
        signals: List[EmpathySignal] = []
        for pattern, weight, label in self._PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                signals.append(EmpathySignal(name=label, weight=weight, evidence=pattern))
        return signals

    def decide(self, signals: List[EmpathySignal], user_text: str) -> EmpathyDecision:
        # Score global 0..1
        score = min(1.0, sum(s.weight for s in signals) / 2.0) if signals else 0.0

        text = user_text.lower()

        # Règles de décision (simples, contrôlables)
        if any("Stress" in s.name for s in signals):
            return EmpathyDecision(mode=EmpathyMode.ENCOURAGE, intensity=max(0.7, score), signals=signals)

        if any("Blocage" in s.name for s in signals) or "pas" in text and "étape" in text:
            return EmpathyDecision(mode=EmpathyMode.STEP_BY_STEP, intensity=max(0.7, score), signals=signals)

        if any("non-compréhension" in s.name.lower() for s in signals) or any("Difficulté" in s.name for s in signals):
            return EmpathyDecision(mode=EmpathyMode.CLARIFY, intensity=max(0.6, score), signals=signals)

        if any("simplification" in s.name.lower() for s in signals):
            return EmpathyDecision(mode=EmpathyMode.REDUCE_COGNITIVE_LOAD, intensity=max(0.6, score), signals=signals)

        # Neutre par défaut
        return EmpathyDecision(mode=EmpathyMode.NEUTRAL, intensity=score, signals=signals)

    def format_response(self, rag_answer: str, decision: EmpathyDecision, course_code: str | None = None) -> str:
        """
        Reformate la réponse RAG (sans ajouter de faits),
        en ajoutant un ton + structure pédagogique.
        """
        prefix = ""
        if decision.mode == EmpathyMode.ENCOURAGE:
            prefix = "Je suis là avec toi 🙂 On va y aller calmement.\n"
        elif decision.mode == EmpathyMode.NORMALIZE_ERROR:
            prefix = "C’est normal de bloquer sur ça — c’est une étape fréquente.\n"
        elif decision.mode == EmpathyMode.CLARIFY:
            prefix = "OK, on clarifie ensemble.\n"
        elif decision.mode == EmpathyMode.STEP_BY_STEP:
            prefix = "Allons-y étape par étape.\n"
        elif decision.mode == EmpathyMode.REDUCE_COGNITIVE_LOAD:
            prefix = "Je te l’explique plus simplement.\n"

        # Structure commune (simple, stable)
        header = f"**Contexte**: {course_code}\n" if course_code else ""
        formatted = (
            f"{prefix}"
            f"{header}"
            f"**Réponse:**\n{rag_answer.strip()}\n"
        )

        # Ajouts pédagogiques non-factuels (questions de clarification, plan d’action)
        if decision.mode in (EmpathyMode.CLARIFY, EmpathyMode.STEP_BY_STEP, EmpathyMode.REDUCE_COGNITIVE_LOAD):
            formatted += "\n**Pour que je t’aide au mieux:**\n"
            formatted += "- Qu’est-ce que tu as déjà essayé ?\n"
            formatted += "- À quel moment précis ça bloque ?\n"

        # Encouragement final léger
        if decision.intensity >= 0.6:
            formatted += "\n**Tu progresses.** Si tu veux, donne-moi un petit exemple de ton code et je te guide.\n"

        return formatted.strip()

    def run(self, user_text: str, rag_answer: str, course_code: str | None = None) -> Tuple[str, EmpathyDecision]:
        signals = self.analyze(user_text)
        decision = self.decide(signals, user_text)
        final = self.format_response(rag_answer, decision, course_code=course_code)
        return final, decision
