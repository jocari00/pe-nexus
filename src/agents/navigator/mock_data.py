"""Mock data for RelationshipNavigator agent.

Provides a realistic sample network of PE professionals, executives, and
intermediaries for demos and testing without requiring real CRM data.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class RelationshipType(str, Enum):
    """Types of professional relationships."""

    WORKED_TOGETHER = "worked_together"  # Former colleagues
    BOARD_TOGETHER = "board_together"  # Co-board members
    INVESTOR_FOUNDER = "investor_founder"  # Investor-portfolio relationship
    ALUMNI = "alumni"  # Same school or company alumni
    MET_AT_CONFERENCE = "met_at_conference"  # Conference/event connection
    MUTUAL_FRIEND = "mutual_friend"  # Introduced by someone
    ADVISOR = "advisor"  # Advisory relationship
    DEAL_COUNTERPARTY = "deal_counterparty"  # Did a deal together


# Relationship strength weights by type (1.0 = strongest)
RELATIONSHIP_WEIGHTS = {
    RelationshipType.WORKED_TOGETHER: 1.0,
    RelationshipType.INVESTOR_FOUNDER: 0.95,
    RelationshipType.BOARD_TOGETHER: 0.90,
    RelationshipType.ADVISOR: 0.85,
    RelationshipType.DEAL_COUNTERPARTY: 0.80,
    RelationshipType.ALUMNI: 0.60,
    RelationshipType.MUTUAL_FRIEND: 0.50,
    RelationshipType.MET_AT_CONFERENCE: 0.40,
}


@dataclass
class MockPerson:
    """A person in the network."""

    id: str
    name: str
    title: str
    company: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_firm_contact: bool = False
    notes: Optional[str] = None


@dataclass
class MockRelationship:
    """A relationship between two people."""

    person_a_id: str
    person_b_id: str
    relationship_type: RelationshipType
    strength: float  # 0.0 - 1.0
    context: Optional[str] = None
    verified: bool = False


def _gen_id() -> str:
    """Generate a consistent UUID for mock data."""
    return str(uuid4())


# =============================================================================
# Mock People - PE Firm Partners (Your Firm)
# =============================================================================

# Fixed IDs for demo consistency
PARTNER_ALEX_ID = "11111111-1111-1111-1111-111111111111"
PARTNER_SARAH_ID = "22222222-2222-2222-2222-222222222222"
PARTNER_MICHAEL_ID = "33333333-3333-3333-3333-333333333333"

MOCK_FIRM_PARTNERS = [
    MockPerson(
        id=PARTNER_ALEX_ID,
        name="Alex Chen",
        title="Managing Partner",
        company="Nexus Capital Partners",
        email="achen@nexuscap.com",
        is_firm_contact=True,
        notes="Focus on technology and healthcare investments",
    ),
    MockPerson(
        id=PARTNER_SARAH_ID,
        name="Sarah Williams",
        title="Partner",
        company="Nexus Capital Partners",
        email="swilliams@nexuscap.com",
        is_firm_contact=True,
        notes="Focus on industrial and consumer investments",
    ),
    MockPerson(
        id=PARTNER_MICHAEL_ID,
        name="Michael Torres",
        title="Principal",
        company="Nexus Capital Partners",
        email="mtorres@nexuscap.com",
        is_firm_contact=True,
        notes="Deal sourcing and execution",
    ),
]

# =============================================================================
# Mock People - Target Company Executives (for TechFlow Solutions)
# =============================================================================

TARGET_CEO_ID = "44444444-4444-4444-4444-444444444444"
TARGET_CFO_ID = "55555555-5555-5555-5555-555555555555"
TARGET_CTO_ID = "66666666-6666-6666-6666-666666666666"

MOCK_TARGET_EXECUTIVES = [
    MockPerson(
        id=TARGET_CEO_ID,
        name="Jennifer Martinez",
        title="CEO",
        company="TechFlow Solutions",
        email="jmartinez@techflow.com",
        linkedin_url="https://linkedin.com/in/jmartinez",
        notes="Founder, exploring strategic options",
    ),
    MockPerson(
        id=TARGET_CFO_ID,
        name="David Park",
        title="CFO",
        company="TechFlow Solutions",
        email="dpark@techflow.com",
        linkedin_url="https://linkedin.com/in/davidpark",
        notes="Former investment banker at Goldman",
    ),
    MockPerson(
        id=TARGET_CTO_ID,
        name="Aisha Johnson",
        title="CTO",
        company="TechFlow Solutions",
        email="ajohnson@techflow.com",
        linkedin_url="https://linkedin.com/in/aishaj",
        notes="Technical co-founder",
    ),
]

# =============================================================================
# Mock People - Intermediaries (Board Members, Advisors, Other Executives)
# =============================================================================

BOARD_MEMBER_1_ID = "77777777-7777-7777-7777-777777777777"
BOARD_MEMBER_2_ID = "88888888-8888-8888-8888-888888888888"
ADVISOR_1_ID = "99999999-9999-9999-9999-999999999999"
OTHER_EXEC_1_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_EXEC_2_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
BANKER_1_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
PORTFOLIO_CEO_1_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
VC_PARTNER_1_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

MOCK_INTERMEDIARIES = [
    MockPerson(
        id=BOARD_MEMBER_1_ID,
        name="Robert Kim",
        title="Board Member",
        company="TechFlow Solutions",
        email="rkim@gmail.com",
        notes="Former CEO of DataSystems Inc, multiple board seats",
    ),
    MockPerson(
        id=BOARD_MEMBER_2_ID,
        name="Lisa Thompson",
        title="Board Member",
        company="TechFlow Solutions",
        email="lthompson@gmail.com",
        notes="Serial entrepreneur, angel investor",
    ),
    MockPerson(
        id=ADVISOR_1_ID,
        name="James Wilson",
        title="Operating Partner",
        company="Summit Equity",
        email="jwilson@summitequity.com",
        notes="Former COO, strong operational background",
    ),
    MockPerson(
        id=OTHER_EXEC_1_ID,
        name="Maria Garcia",
        title="CEO",
        company="CloudSync Inc",
        email="mgarcia@cloudsync.com",
        notes="Stanford MBA, worked with Jennifer Martinez at Oracle",
    ),
    MockPerson(
        id=OTHER_EXEC_2_ID,
        name="Tom Anderson",
        title="Managing Director",
        company="Tech Investment Bank",
        email="tanderson@techib.com",
        notes="Runs software M&A practice",
    ),
    MockPerson(
        id=BANKER_1_ID,
        name="Christine Lee",
        title="Partner",
        company="Advisors LLP",
        email="clee@advisorsllp.com",
        notes="Sell-side advisor, represented TechFlow's last round",
    ),
    MockPerson(
        id=PORTFOLIO_CEO_1_ID,
        name="Kevin O'Brien",
        title="CEO",
        company="DataVault (Nexus Portfolio)",
        email="kobrien@datavault.com",
        notes="Current Nexus portfolio company CEO",
    ),
    MockPerson(
        id=VC_PARTNER_1_ID,
        name="Amanda Foster",
        title="General Partner",
        company="Sequoia Capital",
        email="afoster@sequoia.com",
        notes="Led Series B in TechFlow",
    ),
]

# =============================================================================
# Mock People - Additional Network Nodes
# =============================================================================

EXEC_3_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff"
EXEC_4_ID = "00000000-0000-0000-0000-000000000001"
EXEC_5_ID = "00000000-0000-0000-0000-000000000002"

MOCK_EXTENDED_NETWORK = [
    MockPerson(
        id=EXEC_3_ID,
        name="Steven Chang",
        title="VP Engineering",
        company="Meta",
        email="schang@meta.com",
        notes="Former Stanford classmate of Aisha Johnson",
    ),
    MockPerson(
        id=EXEC_4_ID,
        name="Patricia Davis",
        title="CEO",
        company="HealthTech Partners",
        email="pdavis@healthtech.com",
        notes="Serves on board with Robert Kim",
    ),
    MockPerson(
        id=EXEC_5_ID,
        name="Richard Brown",
        title="Founder",
        company="SaaS Metrics Inc",
        email="rbrown@saasmetrics.com",
        notes="Close friend of Jennifer Martinez from YC batch",
    ),
]

# =============================================================================
# All Mock People Combined
# =============================================================================

MOCK_PEOPLE: list[MockPerson] = (
    MOCK_FIRM_PARTNERS
    + MOCK_TARGET_EXECUTIVES
    + MOCK_INTERMEDIARIES
    + MOCK_EXTENDED_NETWORK
)

# =============================================================================
# Mock Relationships - The Network Edges
# =============================================================================

MOCK_RELATIONSHIPS: list[MockRelationship] = [
    # Direct connections from firm partners
    # Alex Chen's connections
    MockRelationship(
        person_a_id=PARTNER_ALEX_ID,
        person_b_id=BOARD_MEMBER_1_ID,
        relationship_type=RelationshipType.WORKED_TOGETHER,
        strength=0.95,
        context="Worked together at Bain Capital 2010-2014",
        verified=True,
    ),
    MockRelationship(
        person_a_id=PARTNER_ALEX_ID,
        person_b_id=VC_PARTNER_1_ID,
        relationship_type=RelationshipType.DEAL_COUNTERPARTY,
        strength=0.80,
        context="Co-invested in CloudSync Series A",
        verified=True,
    ),
    MockRelationship(
        person_a_id=PARTNER_ALEX_ID,
        person_b_id=PORTFOLIO_CEO_1_ID,
        relationship_type=RelationshipType.INVESTOR_FOUNDER,
        strength=0.95,
        context="Nexus invested in DataVault, Alex is board member",
        verified=True,
    ),
    MockRelationship(
        person_a_id=PARTNER_ALEX_ID,
        person_b_id=OTHER_EXEC_2_ID,
        relationship_type=RelationshipType.MET_AT_CONFERENCE,
        strength=0.45,
        context="Met at SuperReturn 2023",
        verified=False,
    ),
    # Sarah Williams' connections
    MockRelationship(
        person_a_id=PARTNER_SARAH_ID,
        person_b_id=ADVISOR_1_ID,
        relationship_type=RelationshipType.ALUMNI,
        strength=0.70,
        context="Both HBS Class of 2008",
        verified=True,
    ),
    MockRelationship(
        person_a_id=PARTNER_SARAH_ID,
        person_b_id=BANKER_1_ID,
        relationship_type=RelationshipType.DEAL_COUNTERPARTY,
        strength=0.85,
        context="Christine advised on Nexus's last three deals",
        verified=True,
    ),
    MockRelationship(
        person_a_id=PARTNER_SARAH_ID,
        person_b_id=OTHER_EXEC_1_ID,
        relationship_type=RelationshipType.BOARD_TOGETHER,
        strength=0.75,
        context="Both on board of CloudSync",
        verified=True,
    ),
    # Michael Torres' connections
    MockRelationship(
        person_a_id=PARTNER_MICHAEL_ID,
        person_b_id=BOARD_MEMBER_2_ID,
        relationship_type=RelationshipType.MUTUAL_FRIEND,
        strength=0.50,
        context="Introduced by mutual friend at TechCrunch Disrupt",
        verified=False,
    ),
    MockRelationship(
        person_a_id=PARTNER_MICHAEL_ID,
        person_b_id=EXEC_3_ID,
        relationship_type=RelationshipType.ALUMNI,
        strength=0.65,
        context="Both Stanford CS undergrad",
        verified=True,
    ),
    # Intermediary connections to target
    # Robert Kim (Board Member) -> Jennifer Martinez (CEO)
    MockRelationship(
        person_a_id=BOARD_MEMBER_1_ID,
        person_b_id=TARGET_CEO_ID,
        relationship_type=RelationshipType.BOARD_TOGETHER,
        strength=0.90,
        context="Robert is independent board member at TechFlow",
        verified=True,
    ),
    MockRelationship(
        person_a_id=BOARD_MEMBER_1_ID,
        person_b_id=EXEC_4_ID,
        relationship_type=RelationshipType.BOARD_TOGETHER,
        strength=0.80,
        context="Co-board members at HealthTech Partners",
        verified=True,
    ),
    # Lisa Thompson (Board Member) -> Jennifer Martinez (CEO)
    MockRelationship(
        person_a_id=BOARD_MEMBER_2_ID,
        person_b_id=TARGET_CEO_ID,
        relationship_type=RelationshipType.INVESTOR_FOUNDER,
        strength=0.85,
        context="Lisa was angel investor in TechFlow seed round",
        verified=True,
    ),
    MockRelationship(
        person_a_id=BOARD_MEMBER_2_ID,
        person_b_id=TARGET_CFO_ID,
        relationship_type=RelationshipType.BOARD_TOGETHER,
        strength=0.85,
        context="Interact regularly at board meetings",
        verified=True,
    ),
    # Amanda Foster (VC) -> Jennifer Martinez (CEO)
    MockRelationship(
        person_a_id=VC_PARTNER_1_ID,
        person_b_id=TARGET_CEO_ID,
        relationship_type=RelationshipType.INVESTOR_FOUNDER,
        strength=0.90,
        context="Sequoia led TechFlow Series B, Amanda is board observer",
        verified=True,
    ),
    # Maria Garcia -> Jennifer Martinez
    MockRelationship(
        person_a_id=OTHER_EXEC_1_ID,
        person_b_id=TARGET_CEO_ID,
        relationship_type=RelationshipType.WORKED_TOGETHER,
        strength=0.95,
        context="Worked together at Oracle 2008-2012, close friends",
        verified=True,
    ),
    # Richard Brown -> Jennifer Martinez
    MockRelationship(
        person_a_id=EXEC_5_ID,
        person_b_id=TARGET_CEO_ID,
        relationship_type=RelationshipType.ALUMNI,
        strength=0.85,
        context="Same Y Combinator batch W14, stay in touch regularly",
        verified=True,
    ),
    # Christine Lee (Banker) -> David Park (CFO)
    MockRelationship(
        person_a_id=BANKER_1_ID,
        person_b_id=TARGET_CFO_ID,
        relationship_type=RelationshipType.DEAL_COUNTERPARTY,
        strength=0.85,
        context="Christine advised TechFlow on Series C",
        verified=True,
    ),
    # James Wilson (Advisor) -> Robert Kim
    MockRelationship(
        person_a_id=ADVISOR_1_ID,
        person_b_id=BOARD_MEMBER_1_ID,
        relationship_type=RelationshipType.WORKED_TOGETHER,
        strength=0.80,
        context="Both worked at McKinsey early career",
        verified=True,
    ),
    # Steven Chang -> Aisha Johnson (CTO)
    MockRelationship(
        person_a_id=EXEC_3_ID,
        person_b_id=TARGET_CTO_ID,
        relationship_type=RelationshipType.ALUMNI,
        strength=0.75,
        context="Stanford CS PhD program together",
        verified=True,
    ),
    # Portfolio CEO -> Richard Brown
    MockRelationship(
        person_a_id=PORTFOLIO_CEO_1_ID,
        person_b_id=EXEC_5_ID,
        relationship_type=RelationshipType.MET_AT_CONFERENCE,
        strength=0.55,
        context="Met at SaaStr Annual, discussed metrics",
        verified=False,
    ),
    # Additional connections for path diversity
    MockRelationship(
        person_a_id=ADVISOR_1_ID,
        person_b_id=TARGET_CFO_ID,
        relationship_type=RelationshipType.ADVISOR,
        strength=0.60,
        context="James informally advises David on operational matters",
        verified=False,
    ),
    MockRelationship(
        person_a_id=OTHER_EXEC_2_ID,
        person_b_id=BANKER_1_ID,
        relationship_type=RelationshipType.WORKED_TOGETHER,
        strength=0.85,
        context="Both at Tech Investment Bank, different offices",
        verified=True,
    ),
]


def get_mock_person_by_id(person_id: str) -> Optional[MockPerson]:
    """Get a mock person by their ID."""
    for person in MOCK_PEOPLE:
        if person.id == person_id:
            return person
    return None


def get_mock_person_by_name(name: str) -> Optional[MockPerson]:
    """Get a mock person by name (case-insensitive partial match)."""
    name_lower = name.lower()
    for person in MOCK_PEOPLE:
        if name_lower in person.name.lower():
            return person
    return None


def get_firm_partner_ids() -> list[str]:
    """Get all firm partner IDs."""
    return [p.id for p in MOCK_FIRM_PARTNERS]


def get_target_executive_ids() -> list[str]:
    """Get all target company executive IDs."""
    return [p.id for p in MOCK_TARGET_EXECUTIVES]
