# PE-Nexus

### Contributors
- Jordi Carreras
- Juli Delgado
- Bosco Soler

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FAIR](https://img.shields.io/badge/FAIR-78%25-green.svg)

**Full-Lifecycle Private Equity Deal Orchestrator**

A multi-agent autonomous system for private equity deal management, from sourcing through exit.

## Overview

PE-Nexus uses 7 specialized AI agents to automate the PE deal lifecycle:

| Agent | Purpose |
|-------|---------|
| **Intelligence Scout** | Market scanning, deal sourcing, opportunity scoring |
| **Forensic Analyst** | PDF extraction, financial data validation |
| **Relationship Navigator** | Network mapping, warm introduction paths |
| **Legal Guardian** | Contract analysis, risk clause detection |
| **Quant Strategist** | LBO modeling, IRR/MOIC calculations |
| **Adversarial IC** | Bull/Bear debate, investment committee simulation |
| **Value Creation Monitor** | Portfolio KPIs, LP reporting |

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI + Python 3.11+ |
| **Frontend** | Streamlit |
| **Database** | SQLite (local) |
| **Vector Store** | ChromaDB (local) |
| **LLM** | Groq (Llama 3.3 70B) - FREE |
| **Agent Framework** | LangGraph |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/pe-nexus.git
cd pe-nexus

# 2. Create virtual environment (recommended)
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -e .

# 4. Set up environment variables
cp .env.example .env
```

### Configuration (Optional)

Edit `.env` to add your free Groq API key for enhanced AI features:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key_here
```

**Get a free Groq API key at**: https://console.groq.com/keys

> **Note**: The app works fully without an API key - only AI-generated narratives require it.

### Running the Application

You need **two terminals**:

**Terminal 1 - Start Backend:**
```bash
uvicorn src.main:app --reload
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run frontend/app.py
```

Then open **http://localhost:8501** in your browser.

## Features

### What Works Without API Key

| Feature | Without API Key | With Free Groq API Key |
|---------|-----------------|------------------------|
| Deal Scoring | Full calculations | + AI investment thesis |
| LBO Model | IRR, MOIC, projections | + AI commentary |
| Path Finding | BFS algorithm | + AI intro drafts |
| Legal Analysis | Rule-based detection | + AI risk narrative |
| Portfolio KPIs | All metrics | + AI insights |

### Agent Capabilities

**1. Intelligence Scout (Deal Sourcing)**
- Analyzes companies for acquisition potential
- Scores deals on 5 dimensions (news, growth, macro, industry, feasibility)
- Industry-wide opportunity scanning

**2. Relationship Navigator**
- Finds connection paths through professional networks
- Calculates path strength based on relationship quality
- Generates introduction email drafts

**3. Legal Guardian**
- Detects risk clauses (Change of Control, Non-compete, Indemnification)
- Risk severity scoring (Critical/High/Medium/Low)
- Contract portfolio analysis

**4. Quant Strategist**
- Full LBO model with Sources & Uses
- 5-year financial projections
- IRR/MOIC calculations
- Sensitivity analysis tables

**5. Adversarial IC**
- Generates Bull case (investment thesis)
- Generates Bear case (risks and concerns)
- Synthesizes into IC recommendation

**6. Value Creation Monitor**
- Portfolio company KPI tracking
- Variance analysis (actual vs budget)
- LP quarterly report generation

## Project Structure

```
pe-nexus/
├── src/
│   ├── agents/           # 7 specialized agents
│   │   ├── scout/        # Intelligence Scout
│   │   ├── forensic/     # Forensic Analyst
│   │   ├── navigator/    # Relationship Navigator
│   │   ├── guardian/     # Legal Guardian
│   │   ├── strategist/   # Quant Strategist
│   │   ├── ic/           # Adversarial IC (Bull/Bear)
│   │   └── monitor/      # Value Creation Monitor
│   ├── api/              # FastAPI routes
│   ├── core/             # Config, events, traceability
│   ├── db/               # Database models
│   └── schemas/          # Pydantic schemas
├── frontend/
│   ├── app.py            # Streamlit main app
│   ├── pages/            # Individual agent pages
│   └── utils/            # API client, formatters
├── .env.example          # Environment template
└── pyproject.toml        # Dependencies
```

## API Documentation

Once the backend is running, view the interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### "Backend is offline" error
Make sure the FastAPI server is running:
```bash
uvicorn src.main:app --reload
```

### "Module not found" error
Install the package in development mode:
```bash
pip install -e .
```

### LLM features not working
1. Check your `.env` file has a valid `GROQ_API_KEY`
2. Get a free key at https://console.groq.com/keys
3. Restart the backend after changing `.env`

### Windows-specific issues
If you get permission errors, run your terminal as Administrator.

## Architecture

### Deal Pipeline
```
SOURCING → TRIAGE → DILIGENCE → IC_REVIEW → CLOSING → PORTFOLIO → EXITED
                                    ↓
                                REJECTED (from any stage)
```

### Traceability
Every extracted value links back to its source with page numbers and bounding boxes for verification.

## FAIR Principles Compliance

PE-Nexus follows the [FAIR Principles](https://www.go-fair.org/fair-principles/) for research data management:

| Category | Score | Status |
|----------|-------|--------|
| **Findable** | 2.5/4 | Rich metadata, awaiting DOI |
| **Accessible** | 4/4 | Full compliance |
| **Interoperable** | 2/3 | JSON-LD, OpenAPI, standard vocabularies |
| **Reusable** | 3.5/4 | MIT license, full provenance |
| **Overall** | **78%** | Maximum local compliance |

## 🤝 PAIR Principles (AI Responsibility)

PE-Nexus integrates Google's **PAIR (People + AI Research)** principles:
- **Transparency**: Dedicated sidebar explaining AI limitations and data sources.
- **Explainability**: "Why am I seeing this?" tooltips on all AI-generated insights.
- **Control**: User feedback mechanisms and explicit "Human-in-the-loop" decision points.
- **Privacy**: No private data is used for model training; purely inference-based.

For a detailed breakdown of the architecture and compliance for educational review, please see [TEACHER_GUIDE.md](TEACHER_GUIDE.md).


### FAIR Documentation

| File | Purpose |
|------|---------|
| `LICENSE` | MIT license (R1.1) |
| `CITATION.cff` | Academic citation (F2, R1) |
| `codemeta.json` | JSON-LD metadata (F2, I1, A2) |
| `CHANGELOG.md` | Version history (R1.2) |
| `CONTRIBUTING.md` | Contribution guidelines (R1.2) |
| `docs/DATA_DICTIONARY.md` | Schema documentation (R1) |
| `docs/VOCABULARY_MAPPING.md` | Standard vocabularies (I2) |

### FAIR API

Access FAIR metadata programmatically:
```bash
# Get JSON-LD metadata
curl http://localhost:8000/fair/metadata

# Get compliance score
curl http://localhost:8000/fair/score
```

## License

MIT License - Educational project for private equity workflow automation.
