
import streamlit as st
from utils.api_client import get_api_client
from components.theme import get_score_tier

# Get API client
api = get_api_client()

# =============================================================================
# MOCK DATA
# =============================================================================


def _generate_contacts(company_name: str) -> list:
    """Generate deterministic mock contacts based on company name."""
    import hashlib
    
    # Deterministic seed from company name
    seed = int(hashlib.md5(company_name.encode()).hexdigest(), 16)
    
    first_names = ["James", "Robert", "John", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Charles", 
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    def get_name(offset):
        f_idx = (seed + offset) % len(first_names)
        l_idx = (seed + offset + 7) % len(last_names)
        return f"{first_names[f_idx]} {last_names[l_idx]}"

    return [
        {"name": get_name(0), "role": "CEO", "color": "#3B82F6"},
        {"name": get_name(13), "role": "CFO", "color": "#10B981"},
        {"name": get_name(29), "role": "CTO", "color": "#8B5CF6"},
    ]


def get_agent_data(company_id: str, base_revenue: float) -> dict:
    """Generate agent data variations based on company name hash."""
    import hashlib
    import random
    
    # Deterministic seed
    company_name = company_id.replace("_", " ").title() # Approximate name if not passed
    seed = int(hashlib.md5(company_name.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    
    # 1. SCOUT DATA
    base_score = rng.uniform(4.0, 9.5)
    priority = "HIGH" if base_score > 7.5 else "MEDIUM" if base_score > 5.5 else "LOW"
    
    fit_grades = ["A", "A-", "B+", "B", "C+"]
    industry_fit = fit_grades[rng.randint(0, len(fit_grades)-1)]
    
    signals_pool = [
        "PE firm Carlyle exploring strategic review",
        "3 leadership hires in past 90 days",
        "Industry consolidation wave ongoing",
        "Competitor recently acquired at 12x EBITDA",
        "New product launch gaining traction",
        "Regulatory tailwinds in the sector",
        "Patent filing activity up 40%",
        "Mentioned in Gartner Magic Quadrant",
        "Expanding into APAC region",
    ]
    signals = rng.sample(signals_pool, 3)

    scout = {
        "deal_score": round(base_score, 1),
        "priority": priority,
        "industry_fit": industry_fit,
        "signals": signals,
    }

    # 2. NAVIGATOR DATA
    paths = [
        "You → Robert Kim → Jennifer Martinez (CEO)",
        "You → Board Member → CEO",
        "You → Former Colleague → VP Sales → CEO",
        "Direct connection via University Alumni",
        "Cold outreach recommended",
    ]
    relationship_strength = rng.randint(40, 95)
    
    navigator = {
        "path_to_ceo": f"{rng.randint(1, 3)} hops",
        "relationship_strength": relationship_strength,
        "intro_available": relationship_strength > 60,
        "best_path": paths[rng.randint(0, len(paths)-1)],
    }

    # 3. STRATEGIST DATA
    entry_mult = rng.uniform(6.0, 12.0)
    exit_mult_delta = rng.uniform(0.5, 3.0)
    irr = rng.uniform(12.0, 35.0)
    moic = rng.uniform(1.8, 4.5)
    
    strategist = {
        "entry_multiple": round(entry_mult, 1),
        "exit_multiple": round(entry_mult + exit_mult_delta, 1),
        "holding_period": 5,
        "leverage": round(rng.uniform(3.0, 5.5), 1),
        "projected_irr": f"{irr:.1f}%",
        "projected_moic": f"{moic:.1f}x",
        "recommendation": "BUY" if irr > 20 else "HOLD",
    }

    # 4. GUARDIAN DATA
    risks = ["LOW", "MEDIUM", "HIGH"]
    overall_risk = risks[rng.randint(0, 2)]
    
    finding_pool = [
        {"severity": "HIGH", "text": "Change of Control clause"},
        {"severity": "MEDIUM", "text": "Lease restriction"},
        {"severity": "MEDIUM", "text": "IP assignment missing"},
        {"severity": "HIGH", "text": "Pending litigation"},
        {"severity": "LOW", "text": "Incomplete employee records"},
        {"severity": "CRITICAL", "text": "Regulatory investigation pending"},
    ]
    
    num_findings = rng.randint(0, 3)
    findings = rng.sample(finding_pool, num_findings) if num_findings > 0 else []
    
    if overall_risk == "LOW":
        findings = [f for f in findings if f['severity'] in ['LOW', 'MEDIUM']]
    elif overall_risk == "HIGH" and not any(f['severity'] == 'CRITICAL' for f in findings):
        findings.append({"severity": "HIGH", "text": "Customer concentration > 30%"})

    guardian = {
        "overall_risk": overall_risk,
        "critical_flags": sum(1 for f in findings if f['severity'] == 'CRITICAL'),
        "high_flags": sum(1 for f in findings if f['severity'] == 'HIGH'),
        "findings": findings,
    }

    # 5. IC DATA
    confidence = rng.randint(40, 95)
    recs = ["APPROVE", "APPROVE WITH CONDITIONS", "FURTHER ANALYSIS", "PASS"]
    rec = recs[0] if confidence > 80 else recs[1] if confidence > 70 else recs[2] if confidence > 50 else recs[3]
    
    ic = {
        "recommendation": rec,
        "confidence": confidence,
        "thesis": f"Strong platform investment opportunity in the {rng.choice(['SMB', 'Enterprise', 'Mid-market'])} space.",
        "conditions": ["Negotiate Change of Control", "Secure CTO retention"] if "CONDITIONS" in rec else [],
        "next_steps": ["Management presentation", "Legal review"],
    }
    
    # Overrides for specific detailed mocks (optional, to keep some fixed demo scenarios if desired)
    # But for now, fully dynamic is better to solve the user's issue.

    return {
        "scout_data": scout,
        "navigator_data": navigator,
        "strategist_data": strategist,
        "guardian_data": guardian,
        "ic_data": ic
    }


def calculate_nexus_metrics(scout, strategist, guardian, ic):
    """Calculate Nexus Score dynamically based on Agent inputs."""
    # 1. Market Score (Scout)
    market_score = scout.get("deal_score", 5) * 10
    
    # 2. Financial Score (Strategist) - Heuristic based on IRR
    irr_str = strategist.get("projected_irr", "15%").replace("%", "")
    try:
        irr = float(irr_str)
    except:
        irr = 15.0
    health_score = min(irr * 4, 100) 
    
    # 3. Risk Score (Guardian) - Raw Risk Level (Lower is better for company, but for Score contribution we invert)
    # If Risk is LOW (20), Safety is 80.
    risk_level = guardian.get("overall_risk", "MEDIUM")
    risk_val = 80 if risk_level == "HIGH" else 50 if risk_level == "MEDIUM" else 20
    safety_score = 100 - risk_val
    
    # 4. Confidence/Returns (IC/Strategist)
    confidence = ic.get("confidence", 50)
    
    # Returns Score (MOIC)
    moic_str = strategist.get("projected_moic", "2.0x").replace("x", "")
    try:
        moic = float(moic_str)
    except:
        moic = 2.0
    returns_score = min(moic * 30, 100) # 3.3x = 100
    
    # Weighted Nexus Score
    # Market (30%) + Health (30%) + Safety (20%) + Confidence (20%)
    weighted_score = (market_score * 0.30) + (health_score * 0.30) + (safety_score * 0.20) + (confidence * 0.20)
    
    return {
        "nexus_score": int(weighted_score),
        "nexus_breakdown": {
            "market": int(market_score),
            "health": int(health_score),
            "risk": int(risk_val), # Display Risk (Low is Good)
            "confidence": int(confidence),
            "returns": int(returns_score),
        }
    }


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_mock_companies():
    """Get companies from API leaderboard endpoint."""
    try:
        # Call the real synthesis API
        response = api.synthesis_leaderboard(min_score=0, limit=50)

        if not response.get("success", False):
            # Fall back to mock data if API fails
            st.warning("Unable to connect to backend. Showing demo data.")
            return _get_fallback_companies()

        # Transform API response to match UI expectations
        companies = []
        for item in response.get("companies", []):
            companies.append({
                "company_id": item.get("company_id", ""),
                "company_name": item.get("company_name", "Unknown"),
                "sector": item.get("sector", "Technology"),
                "industry": item.get("industry", "Technology"),
                "revenue": item.get("revenue", 0),
                "ebitda": item.get("ebitda", 0),
                "margin": item.get("margin", 0),
                "description": item.get("summary", ""),
                "tags": item.get("tags", []),
                "status": item.get("status", "on_track"),
                "nexus_score": item.get("nexus_score", 0),
                "score_tier": item.get("score_tier", "MEDIUM"),
                # Add some defaults for fields that might not be in API response
                "founded": "N/A",
                "employees": 0,
                "headquarters": "N/A",
            })

        return companies

    except Exception as e:
        # Fall back to mock data if there's any error
        st.warning(f"Unable to connect to backend: {str(e)}. Showing demo data.")
        return _get_fallback_companies()


def _get_fallback_companies():
    """Fallback mock data when API is unavailable."""
    base_companies = [
        {
            "company_id": "cyberguard",
            "company_name": "CyberGuard Systems",
            "sector": "Cybersecurity",
            "industry": "Technology",
            "revenue": 45.5,
            "ebitda": 12.4,
            "margin": 27.2,
            "description": "Leading provider of AI-driven threat detection.",
            "founded": "2018",
            "employees": 240,
            "headquarters": "San Francisco, CA",
            "tags": ["HIGH GROWTH", "PE INTEREST"],
            "status": "outperforming"
        },
        {
            "company_id": "techflow",
            "company_name": "TechFlow Solutions",
            "sector": "B2B SaaS",
            "industry": "Technology",
            "revenue": 52.0,
            "ebitda": 13.0,
            "margin": 25.0,
            "description": "Enterprise workflow automation software.",
            "founded": "2019",
            "employees": 180,
            "headquarters": "Austin, TX",
            "tags": ["OUTPERFORMING"],
            "status": "outperforming",
        },
        {
            "company_id": "healthbridge",
            "company_name": "HealthBridge Analytics",
            "sector": "Healthcare IT",
            "industry": "Healthcare",
            "revenue": 38.5,
            "ebitda": 8.5,
            "margin": 22.1,
            "description": "Data analytics for healthcare providers.",
            "founded": "2017",
            "employees": 120,
            "headquarters": "Boston, MA",
            "tags": ["HIGH GROWTH"],
            "status": "on_track",
        },
    ]

    # Calculate scores on the fly for fallback data
    for c in base_companies:
        data = get_agent_data(c["company_id"], c["revenue"])
        metrics = calculate_nexus_metrics(
            data["scout_data"],
            data["strategist_data"],
            data["guardian_data"],
            data["ic_data"]
        )
        c["nexus_score"] = metrics["nexus_score"]
        c["score_tier"] = get_score_tier(metrics["nexus_score"])

    return base_companies


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_mock_company_detail(company_id: str) -> dict:
    """Get detailed company data from API synthesis endpoint."""
    try:
        # Call the real synthesis company API
        response = api.synthesis_company(company_id)

        if not response.get("success", False):
            # Fall back to mock data if API fails
            st.warning("Unable to load company details from backend. Showing demo data.")
            return _get_fallback_company_detail(company_id)

        # Extract data from API response
        company_info = response.get("company", {})
        nexus_score_data = response.get("nexus_score", {})
        market_positioning = response.get("market_positioning", {})
        financial_health = response.get("financial_health", {})
        risk_analysis = response.get("risk_analysis", {})
        verdict = response.get("verdict", {})

        # Transform to match UI expectations
        scout_data = market_positioning.get("scout_data", {})
        navigator_data = market_positioning.get("navigator_data", {})
        current_perf = financial_health.get("current_performance", {})
        returns_proj = financial_health.get("returns_projection", {})
        legal_analysis = risk_analysis.get("legal_analysis", {})
        ic_data = verdict.get("ic_data", {})

        # Prepare data for UI
        company_name = company_info.get("name", "Unknown")

        return {
            "company_id": company_id,
            "company_name": company_name,
            "sector": company_info.get("sector", "Technology"),
            "industry": company_info.get("industry", "Technology"),
            "status": company_info.get("status", "on_track"),
            "revenue": current_perf.get("revenue", 0),
            "ebitda": current_perf.get("ebitda", 0),
            "margin": current_perf.get("margin", 0),
            "description": f"{company_info.get('name', 'Company')} - AI-generated analysis",
            "founded": "N/A",
            "employees": 150,
            "headquarters": "United States",
            "tags": [],
            "contacts": _generate_contacts(company_name),
            "scout_data": scout_data,
            "navigator_data": navigator_data,
            "strategist_data": {
                "entry_multiple": returns_proj.get("entry_multiple", 8.0),
                "exit_multiple": returns_proj.get("exit_multiple", 9.5),
                "holding_period": returns_proj.get("holding_period", 5),
                "leverage": returns_proj.get("leverage", 4.0),
                "projected_irr": returns_proj.get("projected_irr", "20%"),
                "projected_moic": returns_proj.get("projected_moic", "2.5x"),
                "recommendation": returns_proj.get("recommendation", "HOLD"),
            },
            "guardian_data": {
                "overall_risk": legal_analysis.get("overall_risk", "MEDIUM"),
                "critical_flags": legal_analysis.get("critical_flags", 0),
                "high_flags": legal_analysis.get("high_flags", 0),
                "findings": legal_analysis.get("findings", []),
            },
            "ic_data": ic_data,
            "financial_data": current_perf,
            "nexus_score": nexus_score_data.get("score", 0),
            "nexus_breakdown": nexus_score_data.get("breakdown", {}),
            "news": [
                {"author": "Scout Agent", "date": "Today", "title": f"Analysis completed for {company_info.get('name', 'company')}"},
                {"author": "Market Intel", "date": "Yesterday", "title": "Recent market activity detected"},
            ],
            "competitor_news": [
                {"author": "Industry Watch", "date": "2 days ago", "title": "Competitive landscape analysis available"},
            ],
            "competitors": [],
        }

    except Exception as e:
        st.warning(f"Unable to load company details: {str(e)}. Showing demo data.")
        return _get_fallback_company_detail(company_id)



def _generate_news(company_name: str) -> list:
    """Generate mock news based on company name hash."""
    import hashlib
    import random
    
    seed = int(hashlib.md5(company_name.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    
    headlines = [
        f"{company_name} announces strategic partnership with major industry player",
        f"Quarterly earnings beat expectations for {company_name}",
        f"{company_name} expands leadership team with key hires",
        f"Market analysis: {company_name} positioned for growth",
        f"{company_name} launches next-gen product line",
        f"Regulatory approval granted for {company_name}'s core technology",
        f"{company_name} secures Series C funding round",
        f"Analyst upgrade: {company_name} target price raised",
    ]
    
    return [
        {"author": "Scout Agent", "date": "Today", "title": f"Analysis completed for {company_name}"},
        {"author": "Market Intel", "date": "Yesterday", "title": rng.choice(headlines)},
        {"author": "Industry Wire", "date": "3 days ago", "title": rng.choice(headlines)},
    ]


def _generate_competitors(company_name: str, sector: str) -> list:
    """Generate mock competitors."""
    import hashlib
    import random
    
    seed = int(hashlib.md5(company_name.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    
    comps = [
        {"name": f"{sector} Corp", "description": "Legacy incumbent"},
        {"name": f"NextGen {sector}", "description": "VC-backed challenger"},
        {"name": f"Global {sector} Systems", "description": "International player"},
        {"name": f"{company_name} X", "description": "Direct rival"},
    ]
    
    selected = rng.sample(comps, 2)
    for c in selected:
        c["change"] = rng.randint(-15, 25)
        
    return selected


def _get_fallback_company_detail(company_id: str) -> dict:
    """Fallback mock company detail when API is unavailable."""
    companies = {c["company_id"]: c for c in _get_fallback_companies()}
    
    # Try to find existing mock company, otherwise generate dynamic base
    base = companies.get(company_id)
    
    if not base:
        # Dynamic generation for unknown IDs (e.g. from Deal Flow)
        name = company_id.replace("_", " ").replace("-", " ").title()
        base = {
            "company_id": company_id,
            "company_name": name,
            "sector": "Technology",
            "industry": "Technology",
            "revenue": 50.0,
            "ebitda": 10.0,
            "margin": 20.0,
            "description": f"AI-generated analysis for {name}.",
            "founded": "2020",
            "employees": 100,
            "headquarters": "United States",
            "tags": ["PROSPECT"],
            "status": "watch",
        }
    
    company_name = base.get("company_name", "Unknown")

    # Regenerate DYNAMIC agent data
    agent_data = get_agent_data(company_id, base.get("revenue", 50))
    metrics = calculate_nexus_metrics(
        agent_data["scout_data"],
        agent_data["strategist_data"],
        agent_data["guardian_data"],
        agent_data["ic_data"]
    )

    # Financial Data Helper
    financial_data = {
        "revenue": base.get("revenue", 50),
        "ebitda": base.get("ebitda", 10),
        "margin": base.get("margin", 20),
        "revenue_yoy": "+12%",
        "ebitda_yoy": "+18%",
        "margin_change": "+2.5pp",
        "cash": 12.4,
    }

    return {
        **base,
        "contacts": _generate_contacts(company_name),
        **agent_data,
        "financial_data": financial_data,
        "nexus_score": metrics["nexus_score"],
        "nexus_breakdown": metrics["nexus_breakdown"],
        "news": _generate_news(company_name),
        "competitor_news": [
            {"author": "Industry Watch", "date": "2 days ago", "title": f"Competitive landscape heating up in {base.get('sector', 'Tech')}"},
        ],
        "competitors": _generate_competitors(company_name, base.get("Sector", "Tech")),
    }


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_mock_portfolio():
    """Get portfolio companies from Monitor API."""
    try:
        # Call the real monitor API
        response = api.monitor_companies()

        if not response.get("success", False):
            # Fall back to mock data if API fails
            st.warning("Unable to connect to Monitor agent. Showing demo portfolio data.")
            return _get_fallback_portfolio()

        # Transform API response to match UI expectations
        companies = []
        for company in response.get("companies", []):
            companies.append({
                "company_id": company.get("id", ""),
                "company_name": company.get("name", "Unknown"),
                "sector": company.get("sector", company.get("industry", "Technology")),
                "acquisition_date": company.get("acquisition_date", "N/A"),
                "invested_capital": company.get("invested_capital", 0),
                "current_valuation": company.get("current_valuation", 0),
                "irr": company.get("irr", 0),
                "moic": company.get("moic", 1.0),
                "status": company.get("status", "on_track"),
                "description": company.get("description", ""),
                "metrics": {
                    "revenue": company.get("revenue", 0),
                    "ebitda": company.get("ebitda", 0),
                    "margin": company.get("margin", 0),
                },
                "vcp_status": int(company.get("vcp_progress", 0) * 100) if isinstance(company.get("vcp_progress"), float) else company.get("vcp_progress", 50),
            })

        return companies

    except Exception as e:
        st.warning(f"Unable to load portfolio: {str(e)}. Showing demo data.")
        return _get_fallback_portfolio()


def _get_fallback_portfolio():
    """Fallback mock portfolio when API is unavailable."""
    return [
        {
            "company_id": "apex_manufacturing",
            "company_name": "Apex Manufacturing",
            "sector": "Industrial",
            "acquisition_date": "2022-06-15",
            "invested_capital": 45.0,
            "current_valuation": 62.5,
            "irr": 22.5,
            "moic": 1.39,
            "status": "on_track",
            "description": "Precision parts manufacturer for aerospace and defense sectors.",
            "metrics": {"revenue": 85.0, "ebitda": 14.5, "margin": 17.0},
            "vcp_status": 65,
        },
        {
            "company_id": "cloud_health",
            "company_name": "CloudHealth Solutions",
            "sector": "Healthcare IT",
            "acquisition_date": "2023-01-10",
            "invested_capital": 30.0,
            "current_valuation": 38.2,
            "irr": 28.1,
            "moic": 1.27,
            "status": "outperforming",
            "description": "SaaS platform for patient record management and billing.",
            "metrics": {"revenue": 22.0, "ebitda": 4.5, "margin": 20.5},
            "vcp_status": 40,
        },
        {
            "company_id": "nordic_foods",
            "company_name": "Nordic Foods Group",
            "sector": "Consumer",
            "acquisition_date": "2021-11-20",
            "invested_capital": 60.0,
            "current_valuation": 55.0,
            "irr": -4.2,
            "moic": 0.92,
            "status": "at_risk",
            "description": "Premium frozen food manufacturer distributing across Northern Europe.",
            "metrics": {"revenue": 150.0, "ebitda": 12.0, "margin": 8.0},
            "vcp_status": 80,
        }
    ]
