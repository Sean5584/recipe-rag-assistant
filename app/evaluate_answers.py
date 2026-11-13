"""Collect real application answers and summarize human judgments."""
import argparse
from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import sys
import time

from config import APP_DIR

DEFAULT_QUESTIONS = APP_DIR.parent / "experiments" / "qa_benchmark.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("collect", "score"))
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=61,
                        help="Seconds between questions to accommodate API rate limits")
    parser.add_argument("--limit", type=int, help="Maximum new answers to collect")
    args = parser.parse_args()
    if args.interval < 0 or (args.limit is not None and args.limit < 1):
        parser.error("interval 必须非负，limit 必须大于零")
    question_bytes = args.questions.read_bytes()
    questions = json.loads(question_bytes)
    digest = hashlib.sha256(question_bytes).hexdigest()
    if args.results.exists():
        report = json.loads(args.results.read_text(encoding="utf-8"))
        if report["questions_sha256"] != digest:
            parser.error("题集已变化，请指定新的结果文件")
    else:
        report = {"questions_sha256": digest, "answers": {}}
    answers = report["answers"]
    if args.mode == "score":
        for label, group in (
            ("答案正确率", [q for q in questions if q.get("answerable", True)]),
            ("拒答正确率", [q for q in questions if not q.get("answerable", True)]),
        ):
            grades = [answers.get(q["id"], {}).get("correct") for q in group]
            graded = sum(type(grade) is bool for grade in grades)
            correct = sum(grade is True for grade in grades)
            if graded and graded == len(group):
                print(f"{label}: {correct}/{graded} ({correct / graded:.1%})")
            else:
                print(f"{label}: 已判分 {graded}/{len(group)}，其中 {correct} 题通过；未完成")
        return

    pending = [q for q in questions if q["id"] not in answers][:args.limit]
    if not pending:
        print("题集已全部采集。")
        return
    from main import RecipeRAGSystem
    from openai import APIError

    system = RecipeRAGSystem()
    system.initialize_system()
    system.build_knowledge_base()
    for i, question in enumerate(pending):
        if i:
            time.sleep(args.interval)
        try:
            with redirect_stdout(sys.stderr):
                answer = system.ask_question(question["question"])
        except APIError as exc:
            status = getattr(exc, "status_code", None)
            raise SystemExit(f"{question['id']} 未采集：API 状态 {status or '连接错误'}。已保存前序结果，可重跑续接。") from None
        answers[question["id"]] = {**question, "actual": answer, "correct": None}
        temp = args.results.with_suffix(args.results.suffix + ".tmp")
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(args.results)
        print(f"已保存 {question['id']}（{len(answers)}/{len(questions)}）", flush=True)


if __name__ == "__main__":
    main()
