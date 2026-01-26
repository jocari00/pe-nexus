#!/usr/bin/env python3
"""
PE-Nexus Data Seeding Script

Creates sample data for testing and development:
- Sample deals in various stages
- Sample persons for relationship graph
- Sample relationships
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from uuid import uuid4


SAMPLE_DEALS = [
    {
        "deal_name": "TechFlow Systems Acquisition",
        "target_name": "TechFlow Systems",
        "target_description": "Enterprise SaaS platform for workflow automation",
        "target_headquarters": "San Francisco, CA",
        "industry_sector": "Technology",
        "industry_sub_sector": "Enterprise Software",
        "source_type": "auction",
        "source_description": "Goldman Sachs-led process",
        "stage": "DILIGENCE",
        "deal_score": 8.2,
    },
    {
        "deal_name": "MediCare Plus Platform",
        "target_name": "MediCare Plus",
        "target_description": "Healthcare technology platform for patient engagement",
        "target_headquarters": "Boston, MA",
        "industry_sector": "Healthcare",
        "industry_sub_sector": "HealthTech",
        "source_type": "proprietary",
        "source_description": "Industry conference introduction",
        "stage": "TRIAGE",
        "deal_score": 7.5,
    },
    {
        "deal_name": "Industrial Dynamics Corp",
        "target_name": "Industrial Dynamics",
        "target_description": "Manufacturer of precision industrial components",
        "target_headquarters": "Detroit, MI",
        "industry_sector": "Industrials",
        "industry_sub_sector": "Manufacturing",
        "source_type": "referral",
        "source_description": "Portfolio company CEO referral",
        "stage": "SOURCING",
        "deal_score": 6.8,
    },
    {
        "deal_name": "EcoEnergy Solutions",
        "target_name": "EcoEnergy Solutions",
        "target_description": "Renewable energy infrastructure developer",
        "target_headquarters": "Denver, CO",
        "industry_sector": "Energy",
        "industry_sub_sector": "Renewables",
        "source_type": "proprietary",
        "source_description": "Direct outreach",
        "stage": "IC_REVIEW",
        "deal_score": 8.7,
    },
    {
        "deal_name": "DataVault Analytics",
        "target_name": "DataVault Analytics",
        "target_description": "Big data analytics and AI platform",
        "target_headquarters": "Austin, TX",
        "industry_sector": "Technology",
        "industry_sub_sector": "Data Analytics",
        "source_type": "auction",
        "source_description": "JPMorgan-led process",
        "stage": "REJECTED",
        "deal_score": 5.2,
    },
]

SAMPLE_PERSONS = [
    {
        "name": "John Smith",
        "email": "john.smith@techflow.com",
        "title": "CEO",
        "company": "TechFlow Systems",
        "is_firm_contact": False,
    },
    {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@firm.com",
        "title": "Managing Partner",
        "company": "PE Firm",
        "is_firm_contact": True,
    },
    {
        "name": "Michael Chen",
        "email": "michael.chen@stanford.edu",
        "title": "Professor",
        "company": "Stanford GSB",
        "is_firm_contact": False,
    },
    {
        "name": "Emily Davis",
        "email": "emily.davis@techflow.com",
        "title": "CFO",
        "company": "TechFlow Systems",
        "is_firm_contact": False,
    },
    {
        "name": "Robert Wilson",
        "email": "robert.wilson@firm.com",
        "title": "Principal",
        "company": "PE Firm",
        "is_firm_contact": True,
    },
    {
        "name": "Amanda Brown",
        "email": "amanda.brown@boardmember.com",
        "title": "Board Member",
        "company": "TechFlow Systems",
        "is_firm_contact": False,
    },
]

SAMPLE_RELATIONSHIPS = [
    # Sarah (Partner) knows Michael (Professor) from Stanford
    (1, 2, "alumni", 0.8, "Stanford GSB classmates"),
    # Michael knows John (CEO) from board service
    (2, 0, "board", 0.6, "Served on advisory board together"),
    # Sarah knows Amanda directly
    (1, 5, "professional", 0.9, "Previous deal together"),
    # Amanda is on TechFlow board with John
    (5, 0, "board", 0.95, "Board colleagues at TechFlow"),
    # Robert knows Emily from due diligence
    (4, 3, "professional", 0.5, "Met during prior process"),
]


async def seed_deals():
    """Seed sample deals."""
    from src.db.database import get_session_context
    from src.db.models import DealModel

    print("Seeding deals...")

    async with get_session_context() as db:
        for deal_data in SAMPLE_DEALS:
            deal = DealModel(
                id=str(uuid4()),
                **deal_data,
            )
            db.add(deal)

        await db.commit()

    print(f"  Created {len(SAMPLE_DEALS)} sample deals ✓")


async def seed_persons():
    """Seed sample persons for relationship graph."""
    from src.db.database import get_session_context
    from src.db.models import PersonModel

    print("Seeding persons...")

    person_ids = []
    async with get_session_context() as db:
        for person_data in SAMPLE_PERSONS:
            person = PersonModel(
                id=str(uuid4()),
                **person_data,
            )
            db.add(person)
            person_ids.append(person.id)

        await db.commit()

    print(f"  Created {len(SAMPLE_PERSONS)} sample persons ✓")
    return person_ids


async def seed_relationships(person_ids: list):
    """Seed sample relationships."""
    from src.db.database import get_session_context
    from src.db.models import RelationshipModel

    print("Seeding relationships...")

    async with get_session_context() as db:
        for idx_a, idx_b, rel_type, strength, context in SAMPLE_RELATIONSHIPS:
            rel = RelationshipModel(
                id=str(uuid4()),
                person_a_id=person_ids[idx_a],
                person_b_id=person_ids[idx_b],
                relationship_type=rel_type,
                strength=strength,
                context=context,
                verified=True,
            )
            db.add(rel)

        await db.commit()

    print(f"  Created {len(SAMPLE_RELATIONSHIPS)} sample relationships ✓")


async def main():
    """Run the data seeding."""
    print("=" * 60)
    print("PE-NEXUS DATA SEEDING")
    print("=" * 60)
    print()

    # Initialize database
    print("Initializing database...")
    from src.db.database import init_db
    await init_db()
    print("Database initialized ✓")
    print()

    # Seed data
    await seed_deals()
    person_ids = await seed_persons()
    await seed_relationships(person_ids)

    print()
    print("=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print()
    print("Sample data created:")
    print(f"  - {len(SAMPLE_DEALS)} deals in various stages")
    print(f"  - {len(SAMPLE_PERSONS)} persons in relationship graph")
    print(f"  - {len(SAMPLE_RELATIONSHIPS)} relationships")
    print()
    print("Start the API server to interact with the data:")
    print("  uvicorn src.main:app --reload")
    print()


if __name__ == "__main__":
    asyncio.run(main())
