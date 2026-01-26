# PE-Nexus: Teacher's Guide & Architecture Overview

## Executive Summary
**PE-Nexus** is an AI-powered Private Equity Deal Orchestrator designed to demonstrate the application of Multi-Agent Systems (MAS) in financial workflows. This project adheres to **FAIR** (Findable, Accessible, Interoperable, Reusable) and **PAIR** (People + AI Research) principles to ensure robust, ethical, and explainable AI interactions.

---

## 🏗️ Architecture Overview

The system is built on a modern Python stack separating the backend intelligence from the frontend user experience.

### Backend (`src/`)
- **Framework**: FastAPI (High-performance API)
- **Database**: SQLite (Development) / PostgreSQL (Production ready)
- **AI Engine**: Modular Agent System
    - `Scout Agent`: Market intelligence & signals.
    - `Navigator Agent`: Relationship mapping.
    - `Strategist Agent`: Financial modeling (LBO/DCF).
    - `Guardian Agent`: Risk & compliance checks.
    - `IC Agent`: Investment Committee logic & synthesis.

### Frontend (`frontend/`)
- **Framework**: Streamlit (Rapid data app development)
- **Key Features**:
    - **Component-Based Architecture**: Refactored for maintainability.
    - **Dynamic Rendering**: UI adapts based on company state and agent findings.
    - **Interactivity**: Deep dives into specific agent reasoning.

### 3. Data Resilience & Deterministic Mocking
To ensure a robust "Demo Experience" without requiring a persistent database, we implemented a deterministic data generation layer:
- **Deterministic IDs**: Company IDs are generated using `uuid5` (namespace hashing) based on the company name. This ensures that "CloudSync Technologies" always yields the exact same ID across system restarts, even without a database.
- **Dynamic Fallback**: If the backend receives a request for an unknown company ID (e.g., a new prospect), it dynamically reconstructs a valid "Prospect View" on the fly using the hashed ID to seed the mock data generator. This eliminates "404 Not Found" errors for generated content.
- **Content Consistency**: All "random" data (financials, news, contacts) is seeded with the company name hash. This means the same company will always show the same "random" data, providing a consistent user experience during grading/demos.

---

## ✅ FAIR Principles Compliance
*See `FAIR_COMPLIANCE_REPORT.md` for the full audit.*

- **Findable**: Data uses unique IDs and standard metadata (schema.org).
- **Accessible**: Open API standards (OpenAPI 3.0), clear license (MIT).
- **Interoperable**: JSON-LD usage, widely accepted data formats (JSON/CSV).
- **Reusable**: Extensive documentation, modular code structure.

---

## 🤝 PAIR Principles (AI Responsibility)
We have integrated Google's **PAIR (People + AI Research)** principles to make the AI "seen" and "trustworthy".

### 1. Transparency & Explainability
- **"Why am I seeing this?"**: Every agent insight includes a tooltip or expander explaining the *source* of the data and the *logic* used.
- **Confidence Scores**: Financial projections and risk assessments display confidence levels to manage user expectations.
- **Model Disclosures**: A dedicated "AI Transparency" sidebar explains that agents use specific data sources (public news, internal CRM) and do not leak private data.

### 2. User Control & Feedback
- **Feedback Loops**: "Rate this agent's performance" (Thumbs Up/Down) widgets are implemented on every agent deep-dive page, mimicking RLHF data collection.
- **Overridability**: An explicit "Override / Edit Analysis" button is available on actionable insights, ensuring "Human-in-the-loop" control over final investment memos.
- **Disclaimers**: A prominent warning banner appears on the Browse, Detail, and Portfolio views to remind users that content is AI-generated.

---

## 🚀 How to Run (For Grading)

### Prerequisites
- Python 3.10+
- `pip`

### Step 1: Install Dependencies
```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

### Step 2: Run the Frontend (Demo Mode)
The frontend works in "Mock Mode" by default if the backend is not running, allowing for immediate visual verification without complex setup.
```bash
streamlit run frontend/app.py
```

### Step 3: Run the Backend (Optional)
To see the full system in action with the API:
```bash
python src/main.py
```

---

## 📂 Key Files for Review
- `frontend/app.py`: Main entry point (Clean Architecture).
- `frontend/components/agent_views.py`: Implementation of PAIR transparency features.
- `src/agents/`: Core logic for the AI swarm.
- `FAIR_COMPLIANCE_REPORT.md`: Detailed FAIR audit.
