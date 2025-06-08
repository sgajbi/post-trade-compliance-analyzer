import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os

chroma_client = chromadb.Client()
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

collection = chroma_client.get_or_create_collection("portfolio_analysis")

# In-memory collection mapping id -> portfolio_id
portfolio_map = {}


def ingest_portfolio_analysis(portfolio_id, analysis_text):
    # Chunk (for now, treat each line as separate doc)
    lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
    embeddings = embedding_model.encode(lines).tolist()

    ids = [f"{portfolio_id}_{i}" for i in range(len(lines))]
    collection.add(documents=lines, ids=ids, embeddings=embeddings)
    portfolio_map[portfolio_id] = ids

    print(f"[RAG] Ingested {len(lines)} lines for portfolio {portfolio_id}")
    for line in lines:
        print("  →", line)


def query_portfolio(portfolio_id, question, top_k=3):
    results = collection.query(query_texts=[question], n_results=top_k)
    raw_docs = results["documents"][0]

    # Clean and filter noisy lines
    cleaned_docs = [
        line.strip().strip('",')
        for line in raw_docs
        if line.strip() and not line.strip().startswith("risk_drifts")
    ]
    context = "\n".join(cleaned_docs)

    print("context:\n", context)

    prompt = f"""You are a compliance assistant. Based on the following portfolio report:

{context}

Answer the question: "{question}"
"""

    print("prompt:\n", prompt)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise Exception("OPENAI_API_KEY not set")
    client = OpenAI(api_key=openai_api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
