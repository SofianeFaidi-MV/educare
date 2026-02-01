# core/merge_420514_cours_et_exercices.py
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
EMB_DIR = BASE_DIR / "embeddings"

MODEL_NAME = "all-MiniLM-L6-v2"
MODULE_CODE = "420-514"

COURS_JSON = EMB_DIR / f"{MODULE_CODE}_texts.json"
COURS_NPY = EMB_DIR / f"{MODULE_CODE}_embeddings.npy"

EXOS_JSON = EMB_DIR / f"{MODULE_CODE}_exercices_texts.json"
EXOS_NPY = EMB_DIR / f"{MODULE_CODE}_exercices_embeddings.npy"

BACKUP_JSON = EMB_DIR / f"{MODULE_CODE}_texts.backup.json"
BACKUP_NPY = EMB_DIR / f"{MODULE_CODE}_embeddings.backup.npy"


def load_json(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    if not COURS_JSON.exists() or not COURS_NPY.exists():
        raise RuntimeError("COURS manquant. Lance d'abord ingest_420514_urls.py")

    if not EXOS_JSON.exists() or not EXOS_NPY.exists():
        raise RuntimeError("EXERCICES manquant. Lance d'abord ingest_420514_exercices.py")

    # Backup
    shutil.copyfile(COURS_JSON, BACKUP_JSON)
    shutil.copyfile(COURS_NPY, BACKUP_NPY)

    cours_docs = load_json(COURS_JSON)
    exos_docs = load_json(EXOS_JSON)

    print(f"✅ Cours chargé: {len(cours_docs)} chunks (backup créé)")
    print(f"✅ Exercices chargé: {len(exos_docs)} chunks")

    # Fusion
    merged_docs = cours_docs + exos_docs

    # Recalcule embeddings sur tout (plus sûr que de concat si on change un param)
    model = SentenceTransformer(MODEL_NAME)
    texts = [d["text"] for d in merged_docs]
    embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True).astype("float32")

    save_json(COURS_JSON, merged_docs)
    np.save(COURS_NPY, embs)

    print("\n✅ Fusion terminée !")
    print(f" - total chunks: {len(merged_docs)}")
    print(f" - embeddings : {embs.shape}")
    print(f" - fichiers écrits: {COURS_JSON.name}, {COURS_NPY.name}")
    print(f" - backups: {BACKUP_JSON.name}, {BACKUP_NPY.name}")


if __name__ == "__main__":
    main()
