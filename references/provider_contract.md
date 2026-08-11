# Optional provider contract

The local default is RapidOCR (`rapidocr_onnxruntime`). A provider may expose
`extract_text(image_path)`, `classify_media(crop)`, or `summarize(messages)`,
but it must satisfy all of these rules:

- credentials come only from an environment variable such as
  `DEEPSEEK_API_KEY` or `OPENAI_API_KEY`;
- request and response logs contain hashes, counts, and error codes, never raw
  screenshots or complete chat text;
- provider use is opt-in and clearly reported in the quality report;
- failed or low-confidence output remains reviewable and is not silently
  promoted to `Observed`;
- no provider may send a message, publish content, or access a chat database.

The base scripts work offline. An API adapter can be added later without
changing the normalized schema.
