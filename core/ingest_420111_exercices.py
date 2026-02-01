# from __future__ import annotations

# import re
# import time
# from pathlib import Path
# from urllib.parse import urlparse

# import requests
# from bs4 import BeautifulSoup
# from tqdm import tqdm

# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer

# MODULE_CODE = "420-111"
# COLLECTION_NAME = f"{MODULE_CODE}_exercices"

# PERSIST_DIR = Path("embeddings") / "chroma" / COLLECTION_NAME
# PERSIST_DIR.mkdir(parents=True, exist_ok=True)

# URLS = [
#     "https://cegepmv.github.io/420-111/exercices/serie1/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie2/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie3/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie04/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie05/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie06/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie07/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie08/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie09/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie010/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie012/index.html",
#     "https://cegepmv.github.io/420-111/exercices/serie013/index.html",
# ]


# def fetch_html(url: str) -> str:
#     r = requests.get(url, timeout=25, headers={"User-Agent": "EduCareIndexer/1.0"})
#     r.raise_for_status()
#     return r.text


# def clean_text(s: str) -> str:
#     s = re.sub(r"\s+\n", "\n", s)
#     s = re.sub(r"\n{3,}", "\n\n", s)
#     s = re.sub(r"[ \t]{2,}", " ", s)
#     return s.strip()


# def html_to_text(html: str) -> str:
#     soup = BeautifulSoup(html, "lxml")
#     for tag in soup(["script", "style", "nav", "footer", "header"]):
#         tag.decompose()
#     main = soup.find("main") or soup.body or soup
#     return clean_text(main.get_text("\n", strip=True))


# def split_chunks(text: str, max_chars: int = 1200, overlap: int = 120):
#     parts = [p.strip() for p in text.split("\n\n") if p.strip()]
#     chunks, cur = [], ""

#     def flush():
#         nonlocal cur
#         if cur.strip():
#             chunks.append(cur.strip())
#         cur = ""

#     for p in parts:
#         if len(cur) + len(p) + 2 <= max_chars:
#             cur = (cur + "\n\n" + p) if cur else p
#         else:
#             flush()
#             cur = p
#     flush()

#     if overlap > 0 and len(chunks) > 1:
#         out, prev_tail = [], ""
#         for c in chunks:
#             out.append((prev_tail + c).strip())
#             prev_tail = c[-overlap:]
#         chunks = out

#     return chunks


# def url_slug(url: str) -> str:
#     p = urlparse(url)
#     slug = (p.path or "/").strip("/").replace("/", "_")
#     return slug or "root"


# def main():
#     print("📌 Persist dir:", PERSIST_DIR)

#     # Embeddings locaux (pas de clé)
#     embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

#     # Chroma persistant dans embeddings/chroma/...
#     client = chromadb.PersistentClient(
#         path=str(PERSIST_DIR),
#         settings=Settings(anonymized_telemetry=False),
#     )

#     # recrée proprement (optionnel)
#     try:
#         client.delete_collection(COLLECTION_NAME)
#     except Exception:
#         pass

#     col = client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

#     ids, docs, metas = [], [], []

#     for url in tqdm(URLS, desc="Fetch+parse"):
#         html = fetch_html(url)
#         text = html_to_text(html)
#         title = text.split("\n", 1)[0][:120] if text else "Sans titre"

#         chunks = split_chunks(text)
#         for i, ch in enumerate(chunks):
#             ids.append(f"{url_slug(url)}__{i}")
#             docs.append(ch)
#             metas.append(
#                 {
#                     "module": MODULE_CODE,
#                     "kind": "exercices",
#                     "source": url,
#                     "title": title,
#                     "chunk": i,
#                 }
#             )
#         time.sleep(0.25)

#     embs = embedder.encode(docs, batch_size=32, show_progress_bar=True).tolist()

#     col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)

#     print(f"✅ OK: {len(ids)} chunks indexés dans {PERSIST_DIR} (collection={COLLECTION_NAME})")


# if __name__ == "__main__":
#     main()


# core/ingest_420111_exercices_urls.py
from __future__ import annotations

import json
import re
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

# ⚠️ On met un module_code différent pour ne pas écraser le cours
MODULE_CODE = "420-111_exercices"

OUT_JSON = OUT_DIR / f"{MODULE_CODE}_texts.json"
OUT_NPY = OUT_DIR / f"{MODULE_CODE}_embeddings.npy"

EXOS_INDEX_URL = "https://cegepmv.github.io/420-111/exercices/index.html"


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

    if candidates:
        _, root = max(candidates, key=lambda x: x[0])
    else:
        root = soup.body if soup.body else soup

    text = root.get_text(separator="\n", strip=True)
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
            href = a["href"]
            full = urljoin(index_url, href)
            series_urls.append(full)

    # unique + stable sort (Série 1..)
    series_urls = sorted(set(series_urls), key=lambda u: [int(x) for x in re.findall(r"\d+", u)] or [9999])
    return series_urls


def main() -> None:
    BATCH_SIZE = 16

    # nettoyer
    if OUT_JSON.exists():
        OUT_JSON.unlink()
    if OUT_NPY.exists():
        OUT_NPY.unlink()

    urls = discover_series_urls(EXOS_INDEX_URL)
    if not urls:
        raise RuntimeError("Aucune URL 'Série X' détectée sur la page exercices.")

    model = SentenceTransformer(MODEL_NAME)

    all_docs: List[Dict[str, Any]] = []
    all_emb_parts: List[np.ndarray] = []

    for url in urls:
        print(f"📥 {url}")
        html = fetch_html(url)

        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(strip=True) if soup.title else url

        text = extract_main_text(html)
        chunks = chunk_text(text)

        page_docs = [
            {
                "text": c,
                "metadata": {
                    # 👇 on garde "420-111" comme dans ton JSON de cours
                    "module": "420-111",
                    "source": url,
                    "title": page_title,
                    "type": "web",
                    # optionnel mais pratique
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

    print("\n✅ Terminé !")
    print(f" - total chunks: {len(all_docs)}")
    print(f" - texts : {OUT_JSON}")
    print(f" - emb   : {OUT_NPY}")


if __name__ == "__main__":
    main()
