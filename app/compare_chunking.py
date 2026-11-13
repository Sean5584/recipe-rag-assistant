"""Compare Markdown and fixed-window chunking with identical dense retrieval."""
import argparse
import json
from pathlib import Path
from statistics import mean

from config import APP_DIR, DEFAULT_CONFIG
from rag_modules import DataPreparationModule, IndexConstructionModule


def normalize(text: str) -> str:
    return "".join(text.split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path,
                        default=APP_DIR.parent / "experiments" / "retrieval_pilot.json")
    parser.add_argument("--data", type=Path, default=Path(DEFAULT_CONFIG.data_path))
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--size", type=int, default=400)
    parser.add_argument("--overlap", type=int, default=80)
    args = parser.parse_args()
    if args.k < 1 or args.size < 1 or not 0 <= args.overlap < args.size:
        parser.error("需要 k > 0、size > 0 且 0 <= overlap < size")

    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    questions = [row for row in questions if row.get("answerable", True)]
    if not questions or len({row["id"] for row in questions}) != len(questions):
        parser.error("题集不能为空，且问题 ID 不可重复")

    data = DataPreparationModule(str(args.data))
    docs = data.load_documents()
    by_path = {doc.metadata["source_path"]: doc for doc in docs}
    for row in questions:
        doc = by_path.get(row["source"])
        evidence = normalize(row["evidence"])
        if doc is None or not evidence or evidence not in normalize(doc.page_content):
            parser.error(f"{row['id']} 的标注原文无法在指定菜谱中找到：{row['source']}")

    # Build both indexes from the same current corpus without touching the app cache.
    index = IndexConstructionModule(model_name=DEFAULT_CONFIG.embedding_model)
    query_vectors = [index.embeddings.embed_query(row["question"]) for row in questions]
    results = {}
    for strategy in ("markdown", "fixed"):
        chunks = data.chunk_documents(strategy, size=args.size, overlap=args.overlap)
        store = index.build_vector_index(chunks)
        rows = []
        for row, vector in zip(questions, query_vectors):
            evidence = normalize(row["evidence"])
            hits = store.similarity_search_by_vector(vector, k=args.k)
            source_hits = [hit for hit in hits if hit.metadata["source_path"] == row["source"]]
            rows.append({
                "id": row["id"],
                "document_hit": bool(source_hits),
                "evidence_hit": any(evidence in normalize(hit.page_content) for hit in source_hits),
                "retrieved": [{"source": hit.metadata["source_path"], "section": hit.metadata["section"]}
                              for hit in hits],
            })
        results[strategy] = {
            "chunks": len(chunks),
            "mean_chunk_chars": round(mean(len(c.page_content) for c in chunks), 1),
            "document_hits": sum(row["document_hit"] for row in rows),
            "evidence_hits": sum(row["evidence_hit"] for row in rows),
            "document_hit_rate": mean(row["document_hit"] for row in rows),
            "evidence_hit_rate": mean(row["evidence_hit"] for row in rows),
            "per_question": rows,
        }
    print(json.dumps({
        "documents": len(docs), "questions": len(questions), "k": args.k,
        "model": DEFAULT_CONFIG.embedding_model, "fixed_size": args.size,
        "fixed_overlap": args.overlap, "results": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
