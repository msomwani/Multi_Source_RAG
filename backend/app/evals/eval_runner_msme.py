import json
import time
from pathlib import Path
from datetime import datetime

from app.retrieval.dense import dense_retrieve
from app.retrieval.hybrid import hybrid_retrieve
from app.retrieval.multiquery import multiquery_search
from app.retrieval.rerank import rerank

EVAL_PATH = Path(__file__).parent / "eval_cases_msme.json"
OUT_DIR = Path(__file__).parent / "results"
OUT_DIR.mkdir(exist_ok=True)

PIPELINES = {
    "dense@5": lambda q, cid: dense_retrieve(q, cid, k=5),
    "hybrid@10": lambda q, cid: hybrid_retrieve(q, cid, k=10),
    "multiquery@40": lambda q, cid: multiquery_search(q, cid, k=10, num_queries=4),
    "multiquery+rerank@5": lambda q, cid: rerank(
        q,
        multiquery_search(q, cid, k=10, num_queries=4),
        top_k=5
    ),
}


def contains_keywords(texts, keywords):
    joined = "\n".join(texts).lower()
    return int(all(k.lower() in joined for k in keywords))


def run():
    evals = json.loads(EVAL_PATH.read_text())
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUT_DIR / f"msme_eval_{ts}.json"

    print(f"\n✅ Loaded eval cases: {len(evals)}")
    print(f"📍 Pipelines: {list(PIPELINES.keys())}")
    print(f"💾 Output → {out_file}\n")

    results = {}

    for case in evals:
        print(f"🧪 CASE: {case['name']}")
        print(f"Q: {case['question']}")

        results[case["name"]] = {}

        for pname, fn in PIPELINES.items():
            t0 = time.time()
            try:
                docs = fn(case["question"], case["conversation_id"])
            except Exception as e:
                print(f"  ❌ {pname} failed: {e}")
                results[case["name"]][pname] = {
                "latency_ms": None,
                "keywords_ok": 0,
                "top_sources": [],
                "error": str(e),
                }
                continue

            dt = (time.time() - t0) * 1000

            texts = [d.get("text", "") for d in docs]
            sources = [d.get("source", "unknown") for d in docs]

            kw = contains_keywords(texts, case["expected_keywords"])

            results[case["name"]][pname] = {
                "latency_ms": round(dt, 1),
                "keywords_ok": kw,
                "top_sources": sources[:3],
            }

            print(
                f"  ✅ {pname:<22} "
                f"{dt:>6.1f} ms | kw={kw} | top={sources[:2]}"
            )

        print()

    json.dump(results, out_file.open("w"), indent=2)
    print(f"\n✅ Saved results to {out_file}\n")


if __name__ == "__main__":
    run()
