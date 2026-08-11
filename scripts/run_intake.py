"""Advance a one-question-at-a-time intake session."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


QUESTIONS = [
    ("owner_alias", "What alias should represent the owner?", "owner"),
    ("subject_alias", "What alias should represent the other participant?", "subject"),
    ("relationship", "How would you describe the relationship?", "unknown"),
    ("relationship_period", "What period or life stage does this relationship cover?", "unknown"),
    ("owner_context", "What are the owner's school or organization, student/work status, and role?", "unknown"),
    ("subject_context", "What are the subject's school or organization, student/work status, and role?", "unknown"),
    ("shared_experiences", "Which shared experiences should be remembered?", "skip"),
    ("key_events", "Which relationship milestones or turning points matter?", "skip"),
    ("inside_jokes", "Which important stories or inside jokes are safe to retain?", "skip"),
    ("expression_habits", "Which expression habits should the generated simulation preserve?", "skip"),
    ("privacy_boundary", "What privacy boundary and output use should apply?", "local_only"),
]


def normalize_answer(answer: str) -> tuple[str, str]:
    clean = answer.strip()
    if clean.lower() in {"unknown", "不想提供", "跳过", "skip", "unknown."}:
        return "unknown", "Unknown"
    return clean, "UserProvided"


def advance(state_path: str | Path, answer: str | None = None) -> dict:
    path = Path(state_path).expanduser().resolve()
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"index": 0, "answers": []}
    if answer is not None:
        if state["index"] >= len(QUESTIONS):
            return {"done": True, "state": state}
        key, _, _ = QUESTIONS[state["index"]]
        value, label = normalize_answer(answer)
        state["answers"].append({"field": key, "value": value, "label": label})
        state["index"] += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    if state["index"] >= len(QUESTIONS):
        state["confirmed"] = False
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"done": True, "state": state, "message": "Show the draft summary and request confirmation before generation."}
    key, question, recommendation = QUESTIONS[state["index"]]
    return {"done": False, "field": key, "question": question, "recommended_answer": recommendation, "state": state}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--answer")
    args = parser.parse_args()
    print(json.dumps(advance(args.state, args.answer), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
