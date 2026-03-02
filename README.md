# Digital FTE: Personal AI Employee (Bronze Tier)

> **"Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop."**

This repository contains the foundation for a **Digital Full-Time Equivalent (FTE)**—an autonomous agent system designed to proactively manage personal and business affairs. This project was built for the **Personal AI Employee Hackathon 0**, successfully completing the **Bronze Tier** requirements (The Foundation).

Unlike traditional chatbots, this system uses a "Sense-Think-Act" loop to monitor digital environments, reason through tasks via Claude Code, and maintain a persistent state within an Obsidian "Memory" vault.

---

## Architecture: The "Local-First" Stack

The system is built on four modular pillars:

1. **The Brain (Reasoning):** [Claude Code](https://www.google.com/search?q=https://docs.anthropic.com/en/docs/agents-and-tools/claude-code) acts as the primary executor, handling high-level reasoning and task completion.
2. **The Memory (GUI/Dashboard):** An **Obsidian Vault** (`AI_Employee_Vault/`) provides a human-readable interface and a structured filesystem for the AI's long-term memory.
3. **The Senses (Watchers):** A Python **Sentinel Script** (`watcher.py`) that monitors external triggers and populates the AI's inbox.
4. **The Strategy (Handbook):** A `Company_Handbook.md` that defines the AI's persona, rules of engagement, and standard operating procedures (SOPs).

---

## Repository Structure

```text
.
├── README.md               # Main project documentation & setup
├── CLAUDE.md               # Specific AI behavior guidelines for Claude Code
└── AI_Employee_Vault/      # The core Obsidian "Brain" (Open this in Obsidian)
    ├── watcher.py          # Python "Sentinel" monitoring triggers/inputs
    ├── Dashboard.md        # Real-time business health & task overview
    ├── Company_Handbook.md # The AI's Rules of Engagement
    ├── Inbox/              # Raw, unprocessed data captured by watchers
    ├── Needs_Action/       # Active tasks for the AI to process
    ├── Plans/              # AI-generated implementation strategies
    ├── Done/               # Historical archive of completed tasks
    ├── Logs/               # System execution & audit history
    └── .obsidian/          # Obsidian configuration & workspace settings

```

---

## Getting Started (Bronze Tier Setup)

### 1. Prerequisites

- **Python 3.13+**
- **Node.js v24+**
- **Obsidian v1.10.6+**
- **Claude Code** (Active subscription required)

### 2. Installation & Vault Setup

Clone the repository and prepare the environment:

```bash
git clone https://github.com/your-username/digital-fte-bronze.git
cd digital-fte-bronze

```

1. **Open Obsidian:** Choose "Open folder as vault" and select the `AI_Employee_Vault/` directory.
2. **Configure Rules:** Open `Company_Handbook.md` in Obsidian and customize the "Rules of Engagement" to fit your specific needs.

### 3. Running the "Senses"

Start the watcher script to begin monitoring for tasks:

```bash
cd AI_Employee_Vault
python watcher.py

```

### 4. Initializing the "Brain"

In a separate terminal, run Claude Code from within the `AI_Employee_Vault` directory:

```bash
claude

```

_Note: Claude Code will use the `CLAUDE.md` file in the root to understand its role as your Digital FTE._

---

## Bronze Tier Features Implemented

- [x] **Obsidian Core Dashboard:** A centralized `Dashboard.md` for monitoring business health and bottlenecks.
- [x] **Automated Inbox:** `watcher.py` successfully detects new inputs and creates actionable Markdown files in the `/Inbox`.
- [x] **Structured Task Lifecycle:** A defined workflow where tasks move from `Inbox` → `Needs_Action` → `Plans` → `Done`.
- [x] **Agentic Reasoning:** Integration with Claude Code to perform autonomous file manipulation and decision-making.
- [x] **Company Handbook:** Established SOPs that ensure the AI acts according to predefined business logic and safety constraints.

---

## Security & Privacy

- **Local-First:** All task data, personal notes, and logs stay within your local Obsidian vault.
- **Human-in-the-Loop:** Sensitive tasks (like payments or public posts) are designed to stop in the `Needs_Action` folder until a human moves them to an "Approved" state (Future Tier logic).
- **Credential Safety:** All API keys should be stored in a `.env` file (not tracked by Git).

---

## Future Roadmap (Silver & Gold Tiers)

- **Silver:** Integrate WhatsApp/Telegram watchers and implement a daily "Human-in-the-loop" approval folder.
- **Gold:** The "Monday Morning CEO Briefing"—an autonomous audit of bank transactions and weekly revenue reports.
- **Platinum:** 24/7 Cloud deployment using PM2 process management for zero-downtime autonomy.
