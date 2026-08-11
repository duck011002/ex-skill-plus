# ex.skill-plus

`ex.skill-plus` is a generic local Agent Skill that turns reviewed chat
captures into evidence-bounded summary, persona, style, relationship, profile,
and memory documents. It is an Agent Skill, not a web application: the
standard entry point is the YAML-frontmatter `SKILL.md`, and the bundled Python
scripts run locally on Windows, macOS, or Linux.

## Input

- a screenshot directory plus `manifest.json` (or a directory where the
  manifest is auto-built);
- CSV, HTML, JSON, or JSONL exports, which skip OCR but use the same normalized
  message schema.

RapidOCR is the default local OCR engine. Optional LLM/provider adapters are
documented but never receive a key from source files; credentials must come
from environment variables. Raw screenshots and complete private transcripts
must stay outside public Git history.

## Quick start

```powershell
python scripts/build_manifest.py C:\path\to\screenshots
python scripts/clean_captures.py --input C:\path\to\screenshots --output C:\path\to\cleaned --ocr rapidocr
python scripts/run_intake.py --state C:\path\to\private\intake.json
# ask the printed question, then repeat with --answer "..."
python scripts/build_profile.py --input C:\path\to\cleaned\normalized_messages.jsonl --profile-input C:\path\to\private\profile_input.json --output C:\path\to\private\generated --slug subject --confirmed
python scripts/validate_evidence.py C:\path\to\private\generated\profiles\subject\evidence_map.jsonl
```

The intake intentionally asks one question per turn. `unknown`, `不想提供`,
and `跳过` are valid answers. A draft summary must be shown and confirmed
before generated documents are written.

## Output contract

Each generated object contains `SKILL.md`, `summary.md`, `persona.md`,
`style.md`, `relationship.md`, `profile.md`, `memory.md`,
`evidence_map.jsonl`, `quality_report.md`, `corrections.md`, and a `versions/`
directory. Facts are labeled `Observed`, `Pattern`, `UserProvided`, or
`Unknown`. School, job, age, MBTI, identity, and relationship status are never
guessed from language.

## Testing

```powershell
python -m unittest discover -s tests -v
```

The public fixture is synthetic and intentionally unreadable. The 500-page
personal capture used for local acceptance testing is excluded from this
repository.

## License

MIT. See [LICENSE](LICENSE).
