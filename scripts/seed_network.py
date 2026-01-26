#!/usr/bin/env python3
"""
PE-Nexus Network Seeding Script

Seeds the relationship network from the Navigator agent's mock data
into the database for use with SQL-based path finding.

This populates:
- PersonModel with 15+ people (firm partners, target executives, intermediaries)
- RelationshipModel with 20+ relationships of various types
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def clear_existing_network():
    """Clear existing network data to avoid duplicates."""
    from sqlalchemy import text
    from src.db.database import get_session_context

    print("Clearing existing network data...")

    async with get_session_context() as db:
        await db.execute(text("DELETE FROM relationships"))
        await db.execute(text("DELETE FROM persons"))
        await db.commit()

    print("  Existing network data cleared ✓")


async def seed_persons():
    """Seed persons from mock data."""
    from src.db.database import get_session_context
    from src.db.models import PersonModel
    from src.agents.navigator.mock_data import MOCK_PEOPLE

    print("Seeding persons from mock data...")

    async with get_session_context() as db:
        for person in MOCK_PEOPLE:
            db_person = PersonModel(
                id=person.id,
                name=person.name,
                title=person.title,
                company=person.company,
                email=person.email,
                linkedin_url=person.linkedin_url,
                is_firm_contact=person.is_firm_contact,
                extra_data={"notes": person.notes} if person.notes else {},
            )
            db.add(db_person)

        await db.commit()

    print(f"  Created {len(MOCK_PEOPLE)} persons ✓")

    # Print summary by category
    firm_contacts = [p for p in MOCK_PEOPLE if p.is_firm_contact]
    print(f"    - {len(firm_contacts)} firm contacts (partners)")
    print(f"    - {len(MOCK_PEOPLE) - len(firm_contacts)} external contacts")


async def seed_relationships():
    """Seed relationships from mock data."""
    from src.db.database import get_session_context
    from src.db.models import RelationshipModel
    from src.agents.navigator.mock_data import MOCK_RELATIONSHIPS

    print("Seeding relationships from mock data...")

    async with get_session_context() as db:
        for rel in MOCK_RELATIONSHIPS:
            db_rel = RelationshipModel(
                person_a_id=rel.person_a_id,
                person_b_id=rel.person_b_id,
                relationship_type=rel.relationship_type.value,
                strength=rel.strength,
                context=rel.context,
                verified=rel.verified,
            )
            db.add(db_rel)

        await db.commit()

    print(f"  Created {len(MOCK_RELATIONSHIPS)} relationships ✓")

    # Count by type
    from collections import Counter
    type_counts = Counter(r.relationship_type.value for r in MOCK_RELATIONSHIPS)
    for rel_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    - {rel_type}: {count}")


async def verify_network():
    """Verify the seeded network."""
    from sqlalchemy import select, func
    from src.db.database import get_session_context
    from src.db.models import PersonModel, RelationshipModel

    print("\nVerifying seeded network...")

    async with get_session_context() as db:
        # Count persons
        person_count = await db.scalar(select(func.count()).select_from(PersonModel))
        rel_count = await db.scalar(select(func.count()).select_from(RelationshipModel))

        # Find firm contacts
        firm_query = select(PersonModel).where(PersonModel.is_firm_contact == True)
        firm_result = await db.execute(firm_query)
        firm_contacts = firm_result.scalars().all()

        print(f"  Total persons in database: {person_count}")
        print(f"  Total relationships in database: {rel_count}")
        print(f"\n  Firm contacts (starting points for path finding):")
        for p in firm_contacts:
            print(f"    - {p.name} ({p.title}) - ID: {p.id}")


async def test_path_finding():
    """Test path finding with the seeded data."""
    from src.agents.navigator import RelationshipNavigatorAgent
    from src.agents.navigator.mock_data import PARTNER_ALEX_ID, TARGET_CEO_ID

    print("\nTesting path finding...")

    agent = RelationshipNavigatorAgent()

    # Test finding path from Alex Chen (Partner) to Jennifer Martinez (CEO)
    result = await agent.find_path(
        from_person="Alex Chen",
        to_person="Jennifer Martinez",
        max_hops=3,
    )

    if result.success and result.output_data.get("paths_found", 0) > 0:
        paths = result.output_data.get("paths", [])
        print(f"  Found {len(paths)} path(s) from Alex Chen to Jennifer Martinez ✓")

        if paths:
            best = paths[0]
            print(f"  Best path:")
            print(f"    - Hops: {best['total_hops']}")
            print(f"    - Strength: {best['path_strength']:.3f}")
            print(f"    - Chain: {' -> '.join(n['name'] for n in best['nodes'])}")
    else:
        print("  Path finding test: No paths found (this is unexpected)")
        print(f"    Errors: {result.errors}")


async def main():
    """Run the network seeding."""
    print("=" * 60)
    print("PE-NEXUS NETWORK SEEDING")
    print("=" * 60)
    print()
    print("This script populates the database with the mock network")
    print("data for the RelationshipNavigator agent.")
    print()

    # Initialize database
    print("Initializing database...")
    from src.db.database import init_db
    await init_db()
    print("Database initialized ✓")
    print()

    # Clear existing and seed new
    await clear_existing_network()
    await seed_persons()
    await seed_relationships()

    # Verify
    await verify_network()

    # Test
    await test_path_finding()

    print()
    print("=" * 60)
    print("NETWORK SEEDING COMPLETE")
    print("=" * 60)
    print()
    print("You can now use the Navigator agent to find connection paths.")
    print()
    print("Example API calls:")
    print()
    print('  # Find path between two people')
    print('  curl -X POST http://localhost:8080/agents/navigator/find-path-sync \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"from_person": "Alex Chen", "to_person": "Jennifer Martinez"}\'')
    print()
    print('  # Get introduction suggestion')
    print('  curl -X POST http://localhost:8080/agents/navigator/suggest-intro-sync \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"from_person": "Alex Chen", "to_person": "Jennifer Martinez"}\'')
    print()
    print('  # List all contacts')
    print('  curl http://localhost:8080/agents/navigator/contacts')
    print()


if __name__ == "__main__":
    asyncio.run(main())
