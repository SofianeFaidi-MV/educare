import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDINGS_DIR = BASE_DIR / "embeddings"
EMBEDDINGS_DIR.mkdir(exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"


def extract_text_from_url(url: str) -> str:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Supprimer scripts / styles
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 30]
    return "\n".join(lines)


def chunk_text(text: str, chunk_size=400):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks


def index_url(
    url: str,
    module_code: str,
):
    print(f"🔗 Indexation de {url}")

    text = extract_text_from_url(url)
    chunks = chunk_text(text)

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(chunks)

    texts_payload = [
        {
            "text": chunk,
            "metadata": {
                "source": url,
                "module": module_code,
                "type": "web"
            }
        }
        for chunk in chunks
    ]

    np.save(EMBEDDINGS_DIR / f"{module_code}_embeddings.npy", embeddings)
    with open(EMBEDDINGS_DIR / f"{module_code}_texts.json", "w", encoding="utf-8") as f:
        json.dump(texts_payload, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(chunks)} chunks indexés pour {module_code}")


if __name__ == "__main__":
    index_url(
        url="https://cegepmv.github.io/420-111/index.html",
        module_code="420-111"
    )
