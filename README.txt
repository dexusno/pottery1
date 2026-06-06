POTTERY -> NORWEGIAN PDF — Claude Code scaffold (v5)
Agents: extractor, illustrator, translator, layout-builder, layout-qc, qa-reviewer
Commands: /style-anchor [count] , /rebuild [names | all] , /status

What's new in v5:
- layout-qc agent: a visual/typography critic that inspects the rendered page and
  demands fixes (alignment, gutters, overflow, figure sizing, balance) in a loop
  with the layout-builder before content QA runs. QA render is now 2x (crisp).
- gpt-image-2 prompting upgraded per OpenAI's guide: index-referenced inputs,
  change+preserve split with the preserve list restated, and quality tiers
  (high for label-critical figures, medium otherwise). input_fidelity is omitted
  (locked/high on gpt-image-2 by design).

Setup (PowerShell, from D:\pottery):
  python -m pip install pillow playwright openai   &&   playwright install chromium
  set OPENAI_API_KEY (new terminal) + complete OpenAI Org Verification
  claude  ->  /model claude-opus-4-8
  /style-anchor   -> copy your favorite to style\anchor.png
  /rebuild IMG_7450.JPG   (test one)  ->  /rebuild all
