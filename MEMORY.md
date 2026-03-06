# MEMORY.md — Health Coach Long-Term Memory

---

## Setup

- Agent created: (date)
- Model: anthropic/claude-sonnet-4-6
- Knowledge base: `knowledge/`
- PDF ingestion tool: `tools/ingest-pdf.sh`

## Client Health Context

_(Sana fills this in as she learns about you)_

## Active Protocols

_(Track active fasting periods, exercise programs, etc.)_

## Knowledge Base Index

- `knowledge/lower-back-mobilization.md` — exercises, anatomy, protocols
- `knowledge/oat-fasting-protocol.md` — fasting therapy guide
- `knowledge/fitness-fundamentals.md` — training principles
- `knowledge/nutrition-basics.md` — anti-inflammatory diet, macros
- `knowledge/recovery-sleep.md` — recovery science
- `knowledge/fasting-science-2024-2025.md` — Latest research on IF + cardiovascular effects, metabolic mechanisms
- `knowledge/bp-during-fasting.md` — BP interpretation during fasting
- `knowledge/fasting-psychology-mindset.md` — Neurobiology of fasting, motivation science
- `knowledge/fasting-gut-microbiome.md` — Fasting as microbiome plasticity window

## Tools

- `tools/withings-sync.py` — Fetch Withings BP data → memory/YYYY-MM-DD.md
- `tools/bp-analyze.py` — Smart BP analyzer with fasting context
- `tools/ingest-pdf.sh` — Ingest health PDFs into knowledge base

## Lessons Learned

_(update over time)_
