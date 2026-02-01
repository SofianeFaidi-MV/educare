from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "embeddings"
OUT_DIR.mkdir(exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"
MODULE_CODE = "420-311"

OUT_JSON = OUT_DIR / f"{MODULE_CODE}_texts.json"
OUT_NPY = OUT_DIR / f"{MODULE_CODE}_embeddings.npy"

URLS = [
  "https://cegepmv.github.io/420-311/",
  "https://cegepmv.github.io/420-311/intro/index.html",
  "https://cegepmv.github.io/420-311/intro/revisionpoo/index.html",
  "https://cegepmv.github.io/420-311/sdd/index.html",
  "https://cegepmv.github.io/420-311/complexalgo/index.html",
  "https://cegepmv.github.io/420-311/complexalgo/complexalgo/index.html",
  "https://cegepmv.github.io/420-311/io/index.html",
  "https://cegepmv.github.io/420-311/io/jsonformat/index.html",
  "https://cegepmv.github.io/420-311/io/javaapi/index.html",
  "https://cegepmv.github.io/420-311/genericity/index.html",
  "https://cegepmv.github.io/420-311/genericity/javagen/index.html",
  "https://cegepmv.github.io/420-311/algosearchsort/index.html",
  "https://cegepmv.github.io/420-311/algosearchsort/algosearch/index.html",
  "https://cegepmv.github.io/420-311/algosearchsort/algosort/index.html",
  "https://cegepmv.github.io/420-311/unittests/index.html",
  "https://cegepmv.github.io/420-311/unittests/intojunit/index.html",
  "https://cegepmv.github.io/420-311/threads/index.html",
  "https://cegepmv.github.io/420-311/threads/concepts/index.html",
  "https://cegepmv.github.io/420-311/threads/planifthread/index.html",
  "https://cegepmv.github.io/420-311/ressourcesutiles/index.html",
  "https://cegepmv.github.io/420-311/ressourcesutiles/gestioncodesource/index.html",
  "https://cegepmv.github.io/420-311/ressourcesutiles/maven/index.html",
  "https://cegepmv.github.io/420-311/ressourcesutiles/cartesmentales/index.html",
  "https://cegepmv.github.io/420-311/ressourcesutiles/javaconv/index.html",
]



def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=25, headers={"User-Agent": "EduCareIndexer/1.0"})
    r.raise_for_status()
    return r.text


def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # bruit
    for tag in soup(["nav", "footer", "header", "aside"]):
        tag.decompose()

    # meilleur conteneur
    candidates = []
    for selector in ["main", "article", "section"]:
        for el in soup.select(selector):
            txt = el.get_text(" ", strip=True)
            if len(txt) > 400:
                candidates.append((len(txt), el))

    if candidates:
        _, root = max(candidates, key=lambda x: x[0])
    else:
        # fallback: plus gros div
        best_div, best_len = None, 0
        for d in soup.find_all("div"):
            txt = d.get_text(" ", strip=True)
            if len(txt) > best_len:
                best_len, best_div = len(txt), d
        root = best_div if best_div else (soup.body if soup.body else soup)

    text = root.get_text(separator="\n", strip=True)

    # nettoyage minimal
    text = text.replace("\r", "")
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


def chunk_text(text: str, max_chars: int = 900, overlap_chars: int = 180) -> List[str]:
    text = text.strip()
    if not text:
        return []

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


def title_from_url(url: str) -> str:
    path = url.replace("https://cegepmv.github.io/420-111/", "").strip("/")
    path = path.replace("/index.html", "")
    return path.replace("-", " ").replace("/", " > ")


def main() -> None:
    BATCH_SIZE = 16  # ✅ IMPORTANT: dans main() et la boucle est aussi dans main()

    # nettoyer
    if OUT_JSON.exists():
        OUT_JSON.unlink()
    if OUT_NPY.exists():
        OUT_NPY.unlink()

    model = SentenceTransformer(MODEL_NAME)

    all_docs: List[Dict[str, Any]] = []
    all_emb_parts: List[np.ndarray] = []

    for url in URLS:
        print(f"📥 {url}")
        html = fetch_html(url)

        text = extract_main_text(html)
        chunks = chunk_text(text)

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else url

        page_docs = [
            {
                "text": c,
                "metadata": {
                    "module": "420-311",
                    "source": url,
                    "title": title,
                    "type": "web",
                    "corpus": "cours",
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
        raise RuntimeError("Corpus vide.")

    embeddings = np.vstack(all_emb_parts)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)

    np.save(OUT_NPY, embeddings)

    print("\n✅ Terminé !")
    print(f" - total chunks: {len(all_docs)}")
    print(f" - texts : {OUT_JSON}")
    print(f" - emb   : {OUT_NPY}")


if __name__ == "__main__":
    main()
