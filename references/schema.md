# Normalized schema

`normalized_messages.jsonl` is one JSON object per message:

```json
{
  "message_id": "msg_000001",
  "source_files": ["page_001.png"],
  "sender": {"label": "owner", "confidence": 0.92, "evidence": "right_bubble"},
  "timestamp": {"value": "2026-01-01T12:30:00+08:00", "kind": "observed", "confidence": 0.95},
  "content": "text as actually readable",
  "content_confidence": 0.94,
  "media_type": "text",
  "usefulness": "context",
  "evidence_label": "Observed",
  "page": 1,
  "bbox": [10, 20, 300, 80]
}
```

Allowed `media_type` values are `text`, `image`, `sticker`, `card`, `file`,
`voice`, `video`, `system`, and `unknown`. `sender.label` may be an alias,
`owner`, `subject`, `system`, or `unknown`. A timestamp that is inferred from
nearby UI must use `kind: inferred` and must not be promoted to an observed
exact time.

`profile_input.json` stores intake answers separately from message evidence:

```json
{
  "owner_alias": "owner",
  "subject_alias": "subject",
  "relationship": "unknown",
  "relationship_period": "unknown",
  "owner_context": {"school_or_org": "unknown", "status": "unknown", "role": "unknown"},
  "subject_context": {"school_or_org": "unknown", "status": "unknown", "role": "unknown"},
  "shared_experiences": [],
  "key_events": [],
  "inside_jokes": [],
  "privacy_boundary": "local_only",
  "output_use": "personal_recollection"
}
```
