---
description: Show the processing status of every course image (done/pending, QA result, ignored).
---

Read-only. Do not modify or create anything except by listing.

List every image (*.jpg, *.jpeg, *.png) in the project root (ignore work\,
output\, scripts\, .claude\). For each image report a row:
- name
- DONE if output\<stem>.pdf exists, else PENDING
- QA: the first line of work\<stem>\qa.md if it exists (e.g. RESULT: PASS), else "-"
- IGNORED if the filename appears in ignore.txt, else "-"

Then, if ignore.txt exists, list any lines in it that do not match a real file
(possible typos). Print only the table and that note.
