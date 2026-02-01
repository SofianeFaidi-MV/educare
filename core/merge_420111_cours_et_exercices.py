from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin

import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "embeddings"
OUT_DIR.mkdir(exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"
MODULE_CODE = "420-111"  # ✅ fusion finale dans le module du cours

COURSE_JSON = OUT_DIR / f"{MODULE_CODE}_texts.json"
COURSE_NPY  = OUT_DIR / f"{MODULE_CODE}_embeddings.npy"

# Sauvegardes (recommandé)
BACKUP_JSON = OUT_DIR / f"{MODULE_CODE}_texts.backup.json"
BACKUP_NPY  = OUT_DIR / f"{MODULE_CODE}_embeddings.backup.npy"

EXOS_INDEX_URL = "https://cegepmv.github.io/420-111/exercices/index.html"


# def fetch_html(url: str) -> str:
#     r = requests.get(url, timeout=25, headers={"User-Agent": "EduCareIndexer/1.0"})
#     r.raise_for_status()
#     return r.text

def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=25, headers={"User-Agent": "EduCareIndexer/1.0"})
    if r.status_code == 404:
        print(f"   ⚠️ 404 ignoré: {url}")
        return ""
    r.raise_for_status()
    return r.text



def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for tag in soup(["nav", "footer", "header", "aside"]):
        tag.decompose()

    candidates: List[Tuple[int, Any]] = []
    for selector in ["main", "article", "section"]:
        for el in soup.select(selector):
            txt = el.get_text(" ", strip=True)
            if len(txt) > 200:
                candidates.append((len(txt), el))

    root = max(candidates, key=lambda x: x[0])[1] if candidates else (soup.body or soup)

    text = root.get_text(separator="\n", strip=True)
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln and len(ln) > 2:
            lines.append(ln)

    return "\n".join(lines)


def chunk_text(text: str, max_chars: int = 1200, overlap_chars: int = 150) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) <= 1:
        paras = [p.strip() for p in text.splitlines() if p.strip()]

    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0

    def flush():
        nonlocal cur, cur_len
        if cur:
            chunks.append("\n\n".join(cur).strip())
            cur = []
            cur_len = 0

    for p in paras:
        if len(p) > max_chars:
            sentences = re.split(r"(?<=[.!?])\s+", p)
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if cur_len + len(s) + 2 > max_chars:
                    flush()
                cur.append(s)
                cur_len += len(s) + 2
            continue

        if cur_len + len(p) + 2 > max_chars:
            flush()
        cur.append(p)
        cur_len += len(p) + 2

    flush()

    if overlap_chars > 0 and len(chunks) >= 2:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = overlapped[-1][-overlap_chars:].strip()
            overlapped.append((tail + "\n\n" + chunks[i]).strip())
        chunks = overlapped

    return chunks


def discover_series_urls(index_url: str) -> List[str]:
    html = fetch_html(index_url)
    soup = BeautifulSoup(html, "html.parser")

    series_urls = []
    for a in soup.find_all("a", href=True):
        label = a.get_text(" ", strip=True)
        if re.match(r"^Série\s+\d+\s*$", label, flags=re.IGNORECASE):
            full = urljoin(index_url, a["href"])
            series_urls.append(full)

    # Unique + tri stable (Série 1..)
    series_urls = sorted(set(series_urls), key=lambda u: [int(x) for x in re.findall(r"\d+", u)] or [9999])
    return series_urls


def _doc_key(doc: Dict[str, Any]) -> str:
    """
    Clé de déduplication stable:
    - source + title + hash du texte normalisé (évite doublons à chaque relance)
    """
    meta = doc.get("metadata", {}) or {}
    src = str(meta.get("source", "")).strip()
    title = str(meta.get("title", "")).strip()
    text = (doc.get("text", "") or "").strip()
    norm = re.sub(r"\s+", " ", text)
    h = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]
    return f"{src}||{title}||{h}"


def load_existing_course() -> tuple[List[Dict[str, Any]], np.ndarray]:
    if not COURSE_JSON.exists() or not COURSE_NPY.exists():
        raise RuntimeError(
            "Les fichiers du cours n'existent pas encore.\n"
            "➡️ Génère d'abord le cours: embeddings/420-111_texts.json et embeddings/420-111_embeddings.npy"
        )

    with open(COURSE_JSON, "r", encoding="utf-8") as f:
        docs = json.load(f)

    embs = np.load(COURSE_NPY)
    if len(docs) != embs.shape[0]:
        raise RuntimeError(f"Incohérence: JSON={len(docs)} docs vs NPY={embs.shape[0]} embeddings")

    return docs, embs.astype("float32")


def backup_course_files() -> None:
    # Copie de sécurité avant écrasement
    with open(COURSE_JSON, "r", encoding="utf-8") as f:
        data = f.read()
    BACKUP_JSON.write_text(data, encoding="utf-8")

    np.save(BACKUP_NPY, np.load(COURSE_NPY).astype("float32"))


def main() -> None:
    # 1) Charger cours existant
    course_docs, course_embs = load_existing_course()
    backup_course_files()
    print(f"✅ Cours chargé: {len(course_docs)} chunks (backup créé)")

    # Index de déduplication
    existing_keys = {_doc_key(d) for d in course_docs}

    # 2) Découvrir + parser exercices
    urls = discover_series_urls(EXOS_INDEX_URL)
    if not urls:
        raise RuntimeError("Aucune URL 'Série X' détectée sur la page exercices.")

    model = SentenceTransformer(MODEL_NAME)

    new_docs: List[Dict[str, Any]] = []
    new_texts: List[str] = []

    for url in urls:
        print(f"📥 {url}")
        html = fetch_html(url)
        if not html.strip():
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(strip=True) if soup.title else url

        text = extract_main_text(html)
        chunks = chunk_text(text)

        for c in chunks:
            if not c.strip():
                continue

            doc = {
                "text": c,
                "metadata": {
                    "module": MODULE_CODE,      # ✅ fusion : 420-111
                    "source": url,
                    "title": page_title,
                    "type": "web",
                    "corpus": "exercices",      # ✅ distingue cours vs exercices
                },
            }

            k = _doc_key(doc)
            if k in existing_keys:
                continue

            existing_keys.add(k)
            new_docs.append(doc)
            new_texts.append(c)

        print(f"   ➕ nouveaux chunks ajoutés: {len(new_docs)} (cumul)")

    if not new_docs:
        print("ℹ️ Aucun nouveau chunk d'exercices à ajouter (déjà fusionné).")
        return

    # 3) Embeddings des nouveaux chunks
    BATCH_SIZE = 16
    emb_parts: List[np.ndarray] = []
    for i in range(0, len(new_texts), BATCH_SIZE):
        batch = new_texts[i : i + BATCH_SIZE]
        emb = model.encode(
            batch,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")
        emb_parts.append(emb)

    new_embs = np.vstack(emb_parts)

    # 4) Fusion finale
    merged_docs = course_docs + new_docs
    merged_embs = np.vstack([course_embs, new_embs]).astype("float32")

    # 5) Sauvegarde (écrase le cours avec cours+exercices)
    with open(COURSE_JSON, "w", encoding="utf-8") as f:
        json.dump(merged_docs, f, ensure_ascii=False, indent=2)

    np.save(COURSE_NPY, merged_embs)

    print("\n✅ Fusion terminée !")
    print(f" - total chunks: {len(merged_docs)}")
    print(f" - embeddings : {merged_embs.shape}")
    print(f" - fichiers écrits: {COURSE_JSON.name}, {COURSE_NPY.name}")
    print(f" - backups: {BACKUP_JSON.name}, {BACKUP_NPY.name}")


if __name__ == "__main__":
    main()
