# Evidence and confidence policy

Every generated statement is represented internally as `{text, label,
confidence, source_files, message_ids}`.

`Observed` requires a direct source and both a file and message ID. `Pattern`
requires at least three supporting messages or an explicit aggregate count and
must describe the sample. `UserProvided` is not silently upgraded to
`Observed`. `Unknown` is the correct answer for missing, unreadable,
contradictory, or withheld information.

Confidence is not truth: it describes extraction quality. OCR confidence below
0.80, uncertain bubble ownership, cropped timestamps, stickers, and complex
cards should enter a review queue. A reviewer correction is appended to
`corrections.md`; it does not rewrite the original source evidence.

Never infer a person's school, work, occupation, age, MBTI, diagnosis,
identity, or relationship status from vocabulary, sentiment, or emoji. Never
reconstruct private details from external lookup. Generated text is an AI
simulation and must not be phrased as a message actually sent by the person.
