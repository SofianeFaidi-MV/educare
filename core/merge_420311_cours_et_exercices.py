# core/merge_420210_cours_et_exercices.py
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np


MODULE = "420-311"
EMB_DIR = Path(__file__).resolve().parent.parent / "embeddings"

COURSE_JSON = EMB_DIR / f"{MODULE}_texts.json"
COURSE_NPY  = EMB_DIR / f"{MODULE}_embeddings.npy"

EXO_JSON = EMB_DIR / f"{MODULE}_exercices_texts.json"
EXO_NPY  = EMB_DIR / f"{MODULE}_exercices_embeddings.npy"

BACKUP_COURSE_JSON = EMB_DIR / f"{MODULE}_texts.backup.json"
BACKUP_COURSE_NPY  = EMB_DIR / f"{MODULE}_embeddings.backup.npy"


def load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # 1) Vérifs existence
    for p in [COURSE_JSON, COURSE_NPY, EXO_JSON, EXO_NPY]:
        if not p.exists():
            raise FileNotFoundError(f"Fichier manquant: {p}")

    # 2) Backup des fichiers finaux
    shutil.copy2(COURSE_JSON, BACKUP_COURSE_JSON)
    shutil.copy2(COURSE_NPY, BACKUP_COURSE_NPY)
    print(f"✅ Backup créé: {BACKUP_COURSE_JSON.name}, {BACKUP_COURSE_NPY.name}")

    # 3) Charger
    course_docs = load_json(COURSE_JSON)
    exo_docs = load_json(EXO_JSON)

    course_emb = np.load(COURSE_NPY)
    exo_emb = np.load(EXO_NPY)

    # 4) Contrôles
    if len(course_docs) != course_emb.shape[0]:
        raise ValueError(f"Incohérence cours: docs={len(course_docs)} vs emb={course_emb.shape}")
    if len(exo_docs) != exo_emb.shape[0]:
        raise ValueError(f"Incohérence exos: docs={len(exo_docs)} vs emb={exo_emb.shape}")
    if course_emb.shape[1] != exo_emb.shape[1]:
        raise ValueError(f"Dimension embeddings différente: cours={course_emb.shape} vs exos={exo_emb.shape}")

    # 5) Normaliser/forcer le champ corpus si absent
    for d in course_docs:
        d.setdefault("metadata", {})
        d["metadata"].setdefault("module", MODULE)
        d["metadata"].setdefault("corpus", "cours")

    for d in exo_docs:
        d.setdefault("metadata", {})
        d["metadata"].setdefault("module", MODULE)
        d["metadata"].setdefault("corpus", "exercices")

    # 6) Fusion (cours puis exos)
    merged_docs = course_docs + exo_docs
    merged_emb = np.vstack([course_emb, exo_emb]).astype("float32")

    # 7) Écrire dans les fichiers finaux (ceux utilisés par le chat)
    with open(COURSE_JSON, "w", encoding="utf-8") as f:
        json.dump(merged_docs, f, ensure_ascii=False, indent=2)

    np.save(COURSE_NPY, merged_emb)

    print("✅ Fusion terminée !")
    print(f" - total chunks: {len(merged_docs)}")
    print(f" - embeddings : {merged_emb.shape}")
    print(f" - fichiers écrits: {COURSE_JSON.name}, {COURSE_NPY.name}")


if __name__ == "__main__":
    main()
