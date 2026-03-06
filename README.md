# Sana — AI Health and Fasting Coach for OpenClaw

An evidence-based health coaching agent for [OpenClaw](https://github.com/openclaw/openclaw), specializing in:

- **Therapeutic fasting** (5-day oat-based protocol)
- **Lower back mobilization** & spine health
- **General fitness** & progressive training
- **Nutrition fundamentals** & anti-inflammatory eating
- **BP monitoring** via Withings integration

## What You Get

Sana is a warm, direct, no-BS health coach that runs on your own infrastructure via OpenClaw. She tracks your progress, schedules check-ins, monitors vitals, and adapts recommendations based on your current state.

### Features

- 🩺 **Daily check-ins** with BP tracking and symptom monitoring
- 🥣 **Fasting protocols** with day-by-day guidance, safety thresholds, and refeeding plans
- 🧘 **Movement routines** for lower back mobilization
- 📊 **Withings integration** for automated BP and weight sync
- 📚 **Knowledge base** with curated health science
- 🧠 **Long-term memory** — remembers your history, adapts over time
- ⏰ **Scheduled cron check-ins** during fasting periods
- 📖 **PDF ingestion** — send health PDFs and they get added to the knowledge base

## Prerequisites

- [OpenClaw](https://github.com/openclaw/openclaw) installed and running
- An Anthropic API key (Claude Sonnet 4.5+ recommended)
- A messaging channel configured (Telegram, Signal, Discord, etc.)
- Python 3.10+ (for Withings tools)
- Optional: [Withings](https://www.withings.com/) BP cuff for automated tracking

## Quick Start

```bash
# Sana — AI Health and Fasting Coach for OpenClaw
git clone https://github.com/steckhan/sana-fasting.git
cd sana-fasting

# Sana — AI Health and Fasting Coach for OpenClaw
chmod +x install.sh
./install.sh

# Sana — AI Health and Fasting Coach for OpenClaw
openclaw gateway restart

# Sana — AI Health and Fasting Coach for OpenClaw
# Sana — AI Health and Fasting Coach for OpenClaw
```

## Directory Structure

```
sana-fasting/
├── README.md              ← You are here
├── install.sh             ← Automated setup script
├── agent-config.json      ← OpenClaw agent definition
├── SOUL.md                ← Persona & behavior
├── IDENTITY.md            ← Name, emoji, specialties
├── AGENTS.md              ← Agent logic & capabilities
├── BOOTSTRAP.md           ← First-run onboarding flow
├── HEARTBEAT.md           ← Heartbeat config template
├── USER.md                ← Client profile (fill in on first use)
├── MEMORY.md              ← Long-term memory (starts empty)
├── TOOLS.md               ← Local tool notes
├── protocols/
│   ├── oat-fasting-5day.md
│   └── lower-back-mobilization.md
├── knowledge/             ← Curated health science
│   ├── oat-fasting-protocol.md
│   ├── lower-back-mobilization.md
│   ├── fasting-science-2024-2025.md
│   ├── bp-during-fasting.md
│   ├── fasting-psychology-mindset.md
│   ├── fasting-gut-microbiome.md
│   ├── fitness-fundamentals.md
│   ├── nutrition-basics.md
│   └── recovery-sleep.md
├── tools/
│   ├── withings-auth.py   ← Withings OAuth setup
│   ├── withings-sync.py   ← BP/weight data sync
│   ├── bp-analyze.py      ← Smart BP analyzer
│   ├── ingest-pdf.sh      ← PDF → knowledge base
│   └── pdf-to-memory.sh   ← PDF processing helper
└── memory/                ← Daily session notes (auto-generated)
```

## Withings Setup (Optional)

If you have a Withings BP cuff or scale:

```bash
# Sana — AI Health and Fasting Coach for OpenClaw
# Sana — AI Health and Fasting Coach for OpenClaw
python3 -m venv .venv
source .venv/bin/activate
pip install withings-api requests-oauthlib

# Sana — AI Health and Fasting Coach for OpenClaw
python3 tools/withings-auth.py
# Sana — AI Health and Fasting Coach for OpenClaw

# Sana — AI Health and Fasting Coach for OpenClaw
python3 tools/withings-sync.py
```

## Customization

### Adding Knowledge

Drop health-related PDFs into `inbox-pdfs/incoming/` and tell Sana to ingest them, or run:

```bash
bash tools/ingest-pdf.sh path/to/your-file.pdf
```

### Adjusting Protocols

Edit files in `protocols/` to customize fasting schedules, exercise routines, etc.

### Changing the Persona

Edit `SOUL.md` to adjust Sana's personality, tone, and coaching style.

## Safety

⚠️ **Sana is not a doctor.** She will:
- Never prescribe medication
- Always recommend professional consultation for medical questions
- Flag symptoms that could indicate emergencies
- Add safety caveats to fasting recommendations
- Monitor BP thresholds and alert on RED values

## How Sana Works — Architecture

Sana is a dedicated OpenClaw agent — a second "personality" running alongside your main agent, with its own Telegram bot, workspace, knowledge base, and cron schedule.

### 1. Agent Definition (`openclaw.json`)
Added as `health-coach` to `agents.list` with its own workspace, model (Claude Sonnet), identity (`name: "Sana"`, `emoji: "🏃"`), and memory search paths pointing at `knowledge/`, `protocols/`, `memory/`.

### 2. Separate Telegram Bot
- Create a second Telegram bot via [@BotFather](https://t.me/BotFather)
- Configure as a separate account under `channels.telegram`
- Bind via `bindings[]` → any DM to the Sana bot routes to the `health-coach` agent
- You can also add the `health-coach` agent from your main agent running in OpenClaw.

### 3. Workspace Files
| File | Purpose |
|------|---------|
| `SOUL.md` | Persona, tone, boundaries (warm, direct, evidence-based) |
| `IDENTITY.md` | Name, specialties |
| `AGENTS.md` | Session startup sequence, capabilities, safety rules |
| `USER.md` | Client health profile (goals, conditions, BP baseline) |
| `MEMORY.md` | Long-term facts, knowledge index |
| `HEARTBEAT.md` | Active protocol monitoring + cron schedule |

### 4. Knowledge Base (`knowledge/`)
- 10+ hand-written evidence syntheses (fasting science, BP during fasting, gut-microbiome, psychology, nutrition, lower back mobilization)
- Ingest your own PDFs via `tools/ingest-pdf.sh` — they get chunked and indexed
- All indexed by QMD for semantic search

### 5. Protocols (`protocols/`)
- `oat-fasting-5day.md` — day-by-day checklist with refeeding plan and stop signs
- `lower-back-mobilization.md` — exercise routine with progressions

### 6. Custom Tools (`tools/`)
| Tool | What it does |
|------|-------------|
| `ingest-pdf.sh` | Ingest health PDFs into knowledge base |
| `withings-sync.py` | Fetch BP/weight data from Withings API |
| `bp-analyze.py` | Smart BP classifier (GREEN/YELLOW/RED) with fasting context |
| `withings-auth.py` | Withings OAuth setup flow |

### 7. Cron Jobs
During active protocols (e.g., a 5-day fast), Sana automatically creates scheduled check-ins:
- Morning BP check + energy/symptom survey
- Midday science insights
- Hydration nudges
- Evening wrap-ups with BP comparison
- Refeeding day reminders
- Post-fast follow-up (e.g., 2-week BP check)

## License

MIT — use it, fork it, make it yours.

## Credits

Built with [OpenClaw](https://github.com/openclaw/openclaw) and Claude by Anthropic.

