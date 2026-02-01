# core/ingest_420514_exercices.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "embeddings"
OUT_DIR.mkdir(exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"
MODULE_CODE = "420-514"

OUT_JSON = OUT_DIR / f"{MODULE_CODE}_exercices_texts.json"
OUT_NPY = OUT_DIR / f"{MODULE_CODE}_exercices_embeddings.npy"

# ✅ Pages LAB/EXOS (selon TA liste)
URLS_EXOS = [
    "https://cegepmv.github.io/420-514/nodejsframeworkexpress/lab/index.html",
    "https://cegepmv.github.io/420-514/nodejsframeworkexpress/lab2/index.html",
    "https://cegepmv.github.io/420-514/httprequestdataformat/lab1/index.html",
    "https://cegepmv.github.io/420-514/usets/lab_ts/index.html",
    "https://cegepmv.github.io/420-514/regex/exoregex/index.html",
    "https://cegepmv.github.io/420-514/securapi/labhttpsconfig/index.html",
    "https://cegepmv.github.io/420-514/securapi/labauthsecure/index.html",
    "https://cegepmv.github.io/420-514/docapi/labdocversion/index.html",
    "https://cegepmv.github.io/420-514/dbnosql/labmongodb/index.html",
    "https://cegepmv.github.io/420-514/dbnosql/labmongodbnode/index.html",
    "https://cegepmv.github.io/420-514/tests/labconfigsrvtest/index.html",
]


def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=25, headers={"User-Agent": "EduCareIndexer/1.0"})
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

    text = root.get_text(separator="\n", strip=True).replace("\r", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if len(ln) <= 2:
            continue
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
            cur, cur_len = [], 0

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


def main() -> None:
    BATCH_SIZE = 16

    if OUT_JSON.exists():
        OUT_JSON.unlink()
    if OUT_NPY.exists():
        OUT_NPY.unlink()

    model = SentenceTransformer(MODEL_NAME)

    all_docs: List[Dict[str, Any]] = []
    all_emb_parts: List[np.ndarray] = []

    for url in URLS_EXOS:
        print(f"📥 {url}")
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else url

        text = extract_main_text(html)
        chunks = chunk_text(text)

        page_docs = [
            {
                "text": c,
                "metadata": {
                    "module": MODULE_CODE,
                    "source": url,
                    "title": title,
                    "type": "web",
                    "corpus": "exercices",
                },
            }
            for c in chunks
            if c.strip()
        ]

        texts = [d["text"] for d in page_docs]
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            emb = model.encode(
                batch,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).astype("float32")
            all_emb_parts.append(emb)

        all_docs.extend(page_docs)
        print(f"   ✅ chunks page: {len(page_docs)} | total chunks: {len(all_docs)}")

    if not all_docs:
        raise RuntimeError("Corpus exercices vide.")

    embeddings = np.vstack(all_emb_parts)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)

    np.save(OUT_NPY, embeddings)

    print("\n✅ Terminé EXERCICES !")
    print(f" - total chunks: {len(all_docs)}")
    print(f" - texts : {OUT_JSON}")
    print(f" - emb   : {OUT_NPY}")


if __name__ == "__main__":
    main()
