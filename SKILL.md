---
name: ex-skill-plus
description: Build an evidence-bounded, AI-simulation chat skill from screenshots or exported chat files. Use when a user wants to clean a desktop-chat capture, summarize a conversation, model a participant's communication style, document a relationship, or generate a reusable local SKILL.md without guessing private facts.
---

# ex.skill-plus

This is a local workflow for turning chat evidence into a reusable, generic
persona-and-relationship skill. It is not tied to a person, ex-partner,
colleague, or application. Results are marked as AI simulation and never send
messages or impersonate a real person.

## Workflow

1. **Confirm scope and privacy.** Keep raw screenshots and exports outside a
   public repository. Ask which participant is the owner and which is the
   subject, using aliases rather than legal names. Record the intended output
   and privacy boundary.
2. **Inventory and normalize.** Run `scripts/build_manifest.py` for an image
   directory without a manifest. Run `scripts/clean_captures.py` for images,
   or `scripts/normalize_records.py` for CSV, HTML, JSON, or JSONL. The output
   is a stable `normalized_messages.jsonl` plus a quality report.
3. **Review before interpretation.** Inspect the cleaning preview and review
   queue. Preserve unreadable images, stickers, cards, and uncertain sender or
   time values as `Unknown`; do not turn visual guesses into text.
4. **Run the one-question intake.** Ask exactly one question per turn, give a
   suggested answer when useful, and prefer information already present in
   code or files. Follow `references/intake_protocol.md`. Every answer may be
   `unknown`, `不想提供`, or `跳过`; these are recorded as `Unknown`.
5. **Build evidence-bounded documents.** Run `scripts/build_profile.py` only
   after showing a draft summary and receiving confirmation. It writes
   `profiles/<slug>/summary.md`, `persona.md`, `style.md`, `relationship.md`,
   `profile.md`, `memory.md`, `SKILL.md`, `evidence_map.jsonl`,
   `quality_report.md`, `corrections.md`, and append-only `versions/`.
6. **Validate.** Run `scripts/validate_evidence.py` and
   `scripts/privacy_scan.py`. An `Observed` claim must cite both
   `source_files` and `message_id`. Do not publish raw images, full private
   transcripts, API keys, account IDs, phone numbers, or readable avatars.

## Evidence contract

Use exactly one label for each fact or conclusion:

- `Observed`: directly present in a source message or explicitly supplied by
  the user; include source files and message IDs.
- `Pattern`: a statistic or repeated tendency across multiple records; state
  the sample and uncertainty, and never present it as a biography.
- `UserProvided`: supplied by the owner but not verified in the raw capture.
- `Unknown`: missing, unreadable, conflicting, or intentionally withheld.

Never infer school, employer, occupation, age, MBTI, diagnosis, relationship
status, or identity from writing style. Do not invent text for an image,
sticker, or truncated card. Generated replies must carry an `AI simulation`
label and should not claim to be sent by the subject.

## Host interoperability

The canonical entry point is this YAML-frontmatter `SKILL.md`, compatible with
Agent Skills hosts such as Claude Code, Codex, OpenClaw, and GitHub Copilot.
Scripts are ordinary local Python and do not require a web service. Optional
LLM providers are adapters only; keys come from environment variables and raw
chat data must never be written to logs.

Read the detailed contracts only when needed:

- `references/schema.md` — normalized message and profile fields.
- `references/evidence_policy.md` — source and confidence rules.
- `references/intake_protocol.md` — GrillMe-style one-question interview.
- `references/provider_contract.md` — safe optional OCR/LLM provider boundary.
