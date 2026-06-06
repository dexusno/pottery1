---
name: extractor
description: Reads ONE course sheet image and writes its structure (text + figures) to extract.json. Works for any layout. Use first.
tools: Read, Write
model: inherit
---

Capture the structure of one sheet so it can be rebuilt. Do NOT translate — record
the English exactly. Sheets vary widely (any layout, any text size); describe what
you see, don't assume a format.

Write `work/<stem>/extract.json`:

{
  "source": "<filename>",
  "page_size": [w, h],
  "title": {"text": "<main header, as ONE line — collapse any source line breaks>", "keep_english": true},
  "layout": "<one plain sentence describing this sheet's actual layout>",
  "blocks": [
    {"id": "b1", "role": "heading|step_name|bullet|label|caption|note|question",
     "text": "<verbatim>", "group": "<optional>", "anchor": [x, y]}
  ],
  "crops": [
    {"name": "<snake_case>", "box": [l, t, r, b], "depicts": "<what it shows>",
     "place_near": "<block id/group>", "label_critical": false,
     "preserve": ["<element>", "..."], "text": ["<verbatim text inside the figure, if any>"]}
  ]
}

- `box`/`anchor` are normalized 0..1; err slightly large on `box`.
- `text`: any words that appear INSIDE the figure (e.g. a label on a bottle),
  verbatim. Omit or use [] if the figure has no text.
- `label_critical`: true when the figure's exact composition carries the
  instruction (labels point at specific parts, or it shows a specific stage/step).
- `preserve`: the elements that must survive a restyle, in order. Be exhaustive if
  label_critical; otherwise list the subject and any details that carry meaning.
- Crop a coherent scene as ONE figure — keep elements that belong together (e.g. an
  action and the object it acts on) in the same crop; don't split them into separate
  figures or invent missing pieces.
- `keep_english: true` only on the main title.
Write only the JSON; report the path and a one-line summary.
