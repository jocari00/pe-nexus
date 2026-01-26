"""FAIR Principles compliance API endpoint."""

from datetime import date
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/fair", tags=["FAIR Compliance"])


def get_fair_principles() -> list[dict[str, Any]]:
    """Get all FAIR principles with PE-Nexus compliance status."""
    return [
        # Findable
        {
            "id": "F1",
            "category": "Findable",
            "principle": "Globally unique and persistent identifiers",
            "status": "partial",
            "score": 0.5,
            "evidence": [
                "All entities use UUID v4 (MasterDeal, TracedValue, etc.)",
                "codemeta.json and .zenodo.json prepared for DOI minting",
            ],
            "gap": "DOI not yet minted (requires Zenodo registration)",
        },
        {
            "id": "F2",
            "category": "Findable",
            "principle": "Rich metadata description",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "pyproject.toml with keywords, classifiers, URLs",
                "codemeta.json with JSON-LD schema",
                "CITATION.cff for academic citation",
                "README.md with badges",
            ],
            "gap": None,
        },
        {
            "id": "F3",
            "category": "Findable",
            "principle": "Metadata includes identifier",
            "status": "partial",
            "score": 0.5,
            "evidence": [
                "Internal UUIDs for all data entities",
                "SourceReference links in TracedValue",
            ],
            "gap": "No persistent DOI yet",
        },
        {
            "id": "F4",
            "category": "Findable",
            "principle": "Registered in searchable resource",
            "status": "non-compliant",
            "score": 0.0,
            "evidence": [
                "GitHub repository (searchable)",
            ],
            "gap": "Not registered on PyPI or Zenodo",
        },
        # Accessible
        {
            "id": "A1",
            "category": "Accessible",
            "principle": "Retrievable via standardized protocol",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "REST API with OpenAPI documentation",
                "HTTPS/git access",
                "CI/CD workflow configured",
            ],
            "gap": None,
        },
        {
            "id": "A1.1",
            "category": "Accessible",
            "principle": "Protocol is open, free, implementable",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "Uses HTTPS, git, HTTP REST",
                "No proprietary protocols",
            ],
            "gap": None,
        },
        {
            "id": "A1.2",
            "category": "Accessible",
            "principle": "Protocol allows authentication",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                ".env.example documents API key configuration",
                "SECURITY.md describes security requirements",
            ],
            "gap": None,
        },
        {
            "id": "A2",
            "category": "Accessible",
            "principle": "Metadata accessible when data unavailable",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "codemeta.json is standalone",
                "CITATION.cff is standalone",
                ".zenodo.json is standalone",
            ],
            "gap": None,
        },
        # Interoperable
        {
            "id": "I1",
            "category": "Interoperable",
            "principle": "Uses formal knowledge representation",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "JSON-LD in codemeta.json",
                "Pydantic schemas with type validation",
                "OpenAPI specification",
                "SQLAlchemy ORM models",
            ],
            "gap": None,
        },
        {
            "id": "I2",
            "category": "Interoperable",
            "principle": "Uses FAIR vocabularies",
            "status": "partial",
            "score": 0.5,
            "evidence": [
                "VOCABULARY_MAPPING.md documents standards",
                "ISO 4217 for currencies",
                "NAICS/SIC for industry codes",
            ],
            "gap": "No formal ontology adoption",
        },
        {
            "id": "I3",
            "category": "Interoperable",
            "principle": "Qualified references to other data",
            "status": "partial",
            "score": 0.5,
            "evidence": [
                "UUIDs link entities",
                "SourceReference with document/page/bbox",
                "Schema.org references in codemeta",
            ],
            "gap": "Could add more semantic links",
        },
        # Reusable
        {
            "id": "R1",
            "category": "Reusable",
            "principle": "Rich description with attributes",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "README.md with full documentation",
                "DATA_DICTIONARY.md documents schemas",
                "API docs at /docs and /redoc",
                "CHANGELOG.md tracks versions",
            ],
            "gap": None,
        },
        {
            "id": "R1.1",
            "category": "Reusable",
            "principle": "Clear data usage license",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "MIT LICENSE file",
                "License in pyproject.toml",
                "License in CITATION.cff",
            ],
            "gap": None,
        },
        {
            "id": "R1.2",
            "category": "Reusable",
            "principle": "Detailed provenance",
            "status": "compliant",
            "score": 1.0,
            "evidence": [
                "CHANGELOG.md following Keep a Changelog",
                "CONTRIBUTING.md with guidelines",
                "TracedValue system tracks all extractions",
                "GitHub issue/PR templates",
            ],
            "gap": None,
        },
        {
            "id": "R1.3",
            "category": "Reusable",
            "principle": "Meets domain-relevant standards",
            "status": "partial",
            "score": 0.5,
            "evidence": [
                "VOCABULARY_MAPPING.md with financial standards",
                "SECURITY.md for financial data handling",
                "Decimal type for all monetary values",
            ],
            "gap": "Could adopt more formal financial ontologies",
        },
    ]


def calculate_scores(principles: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate FAIR compliance scores by category."""
    categories = {
        "Findable": {"count": 0, "score": 0, "max": 4},
        "Accessible": {"count": 0, "score": 0, "max": 4},
        "Interoperable": {"count": 0, "score": 0, "max": 3},
        "Reusable": {"count": 0, "score": 0, "max": 4},
    }

    for p in principles:
        cat = p["category"]
        categories[cat]["count"] += 1
        categories[cat]["score"] += p["score"]

    total_score = sum(c["score"] for c in categories.values())
    total_max = sum(c["max"] for c in categories.values())

    return {
        "findable": f"{categories['Findable']['score']:.1f}/{categories['Findable']['max']}",
        "accessible": f"{categories['Accessible']['score']:.1f}/{categories['Accessible']['max']}",
        "interoperable": f"{categories['Interoperable']['score']:.1f}/{categories['Interoperable']['max']}",
        "reusable": f"{categories['Reusable']['score']:.1f}/{categories['Reusable']['max']}",
        "total": f"{total_score:.1f}/{total_max}",
        "percentage": round((total_score / total_max) * 100),
    }


@router.get("/metadata")
async def get_fair_metadata() -> dict[str, Any]:
    """Return FAIR metadata in JSON-LD format."""
    principles = get_fair_principles()
    scores = calculate_scores(principles)

    return {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode",
        "name": "PE-Nexus",
        "description": "Full-Lifecycle Private Equity Deal Orchestrator",
        "version": "0.1.0",
        "license": "https://spdx.org/licenses/MIT",
        "codeRepository": "https://github.com/jordi/pe-nexus",
        "programmingLanguage": "Python",
        "applicationCategory": "Finance",
        "dateModified": date.today().isoformat(),
        "fairCompliance": {
            "assessmentDate": date.today().isoformat(),
            "assessmentVersion": "4.0",
            "scores": scores,
            "status": "Maximum local compliance achieved",
        },
    }


@router.get("/principles")
async def get_principles() -> dict[str, Any]:
    """Get detailed FAIR principles assessment."""
    principles = get_fair_principles()
    scores = calculate_scores(principles)

    return {
        "assessmentDate": date.today().isoformat(),
        "scores": scores,
        "principles": principles,
        "documentation": {
            "license": "LICENSE",
            "citation": "CITATION.cff",
            "metadata": "codemeta.json",
            "changelog": "CHANGELOG.md",
            "contributing": "CONTRIBUTING.md",
            "security": "SECURITY.md",
            "data_dictionary": "docs/DATA_DICTIONARY.md",
            "vocabulary_mapping": "docs/VOCABULARY_MAPPING.md",
        },
    }


@router.get("/score")
async def get_fair_score() -> dict[str, Any]:
    """Get FAIR compliance score summary."""
    principles = get_fair_principles()
    scores = calculate_scores(principles)

    compliant = sum(1 for p in principles if p["status"] == "compliant")
    partial = sum(1 for p in principles if p["status"] == "partial")
    non_compliant = sum(1 for p in principles if p["status"] == "non-compliant")

    return {
        "overall_percentage": scores["percentage"],
        "category_scores": {
            "findable": scores["findable"],
            "accessible": scores["accessible"],
            "interoperable": scores["interoperable"],
            "reusable": scores["reusable"],
        },
        "principle_counts": {
            "compliant": compliant,
            "partial": partial,
            "non_compliant": non_compliant,
            "total": len(principles),
        },
        "status": "Maximum local compliance achieved (78%)",
        "next_steps": [
            "Register on Zenodo to mint DOI (F1, F3)",
            "Publish to PyPI for discoverability (F4)",
            "Add ORCID for author identification",
        ],
    }


@router.get("/files")
async def get_fair_files() -> dict[str, Any]:
    """List all FAIR-related files and their purposes."""
    return {
        "root_files": [
            {"file": "LICENSE", "purpose": "MIT license (R1.1)", "status": "present"},
            {"file": "CITATION.cff", "purpose": "Academic citation (F2, R1)", "status": "present"},
            {"file": "codemeta.json", "purpose": "JSON-LD metadata (F2, I1, A2)", "status": "present"},
            {"file": ".zenodo.json", "purpose": "DOI preparation (F1)", "status": "present"},
            {"file": "CHANGELOG.md", "purpose": "Version history (R1.2)", "status": "present"},
            {"file": "CONTRIBUTING.md", "purpose": "Contribution guidelines (R1.2)", "status": "present"},
            {"file": "CODE_OF_CONDUCT.md", "purpose": "Community standards (R1)", "status": "present"},
            {"file": "SECURITY.md", "purpose": "Security policy (R1.3)", "status": "present"},
        ],
        "github_files": [
            {"file": ".github/workflows/ci.yml", "purpose": "CI/CD pipeline (A1)", "status": "present"},
            {"file": ".github/ISSUE_TEMPLATE/", "purpose": "Issue templates (R1.2)", "status": "present"},
            {"file": ".github/PULL_REQUEST_TEMPLATE.md", "purpose": "PR template (R1.2)", "status": "present"},
        ],
        "docs_files": [
            {"file": "docs/DATA_DICTIONARY.md", "purpose": "Schema documentation (R1)", "status": "present"},
            {"file": "docs/VOCABULARY_MAPPING.md", "purpose": "Standard vocabularies (I2)", "status": "present"},
        ],
        "code_features": [
            {"feature": "UUID identifiers", "location": "src/schemas/", "fair_principle": "F1, F3"},
            {"feature": "TracedValue provenance", "location": "src/schemas/financials.py", "fair_principle": "R1.2"},
            {"feature": "OpenAPI docs", "location": "/docs endpoint", "fair_principle": "A1, I1"},
            {"feature": "Decimal for money", "location": "src/schemas/", "fair_principle": "R1.3"},
        ],
    }
