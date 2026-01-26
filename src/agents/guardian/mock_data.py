"""Mock contract data for LegalGuardian agent development and testing."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ContractType(str, Enum):
    """Types of contracts that can be analyzed."""
    CUSTOMER_AGREEMENT = "customer_agreement"
    EMPLOYMENT = "employment"
    VENDOR = "vendor"
    LEASE = "lease"
    IP_LICENSE = "ip_license"
    LOAN = "loan"
    SHAREHOLDER = "shareholder"
    ACQUISITION = "acquisition"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class MockContract:
    """Represents a contract document for analysis."""
    id: str
    name: str
    contract_type: ContractType
    counterparty: str
    effective_date: str
    expiration_date: Optional[str]
    value: Optional[float]  # Annual contract value
    content: str  # Full text content


# Sample contracts with various clause types for testing
MOCK_CONTRACTS = [
    MockContract(
        id="contract-001",
        name="Enterprise SaaS Agreement - Acme Corp",
        contract_type=ContractType.CUSTOMER_AGREEMENT,
        counterparty="Acme Corporation",
        effective_date="2023-01-15",
        expiration_date="2026-01-14",
        value=2500000.0,
        content="""
ENTERPRISE SOFTWARE LICENSE AND SERVICES AGREEMENT

This Enterprise Software License and Services Agreement ("Agreement") is entered into as of January 15, 2023 ("Effective Date") by and between TechCo Inc., a Delaware corporation ("Provider"), and Acme Corporation, a California corporation ("Customer").

1. LICENSE GRANT
Provider grants to Customer a non-exclusive, non-transferable license to use the Software during the Term.

2. FEES AND PAYMENT
Customer shall pay Provider annual license fees of $2,500,000, payable in quarterly installments.

3. TERM AND TERMINATION
3.1 Initial Term: This Agreement shall commence on the Effective Date and continue for three (3) years.
3.2 Renewal: This Agreement shall automatically renew for successive one (1) year periods unless either party provides written notice of non-renewal at least ninety (90) days prior to the end of the then-current term.

4. CHANGE OF CONTROL
4.1 Definition: "Change of Control" means (a) the sale of all or substantially all of the assets of a party; (b) a merger, consolidation, or reorganization of a party with or into another entity; or (c) any transaction in which more than 50% of the voting power of a party is transferred.

4.2 NOTIFICATION REQUIREMENT: In the event of a Change of Control of Provider, Provider shall notify Customer in writing within thirty (30) days of such Change of Control.

4.3 CUSTOMER TERMINATION RIGHT: Upon a Change of Control of Provider, Customer may terminate this Agreement upon sixty (60) days written notice without penalty. Customer shall be entitled to a pro-rata refund of any prepaid fees for the period following termination.

5. ASSIGNMENT
Neither party may assign this Agreement without the prior written consent of the other party, except that either party may assign this Agreement to a successor in connection with a merger, acquisition, or sale of all or substantially all of its assets, provided that the assignee agrees in writing to be bound by the terms of this Agreement. Notwithstanding the foregoing, Customer's consent to any such assignment by Provider shall not be unreasonably withheld.

6. INTELLECTUAL PROPERTY
6.1 Provider IP: Provider retains all right, title, and interest in the Software and any modifications or improvements thereto.
6.2 Customer Data: Customer retains all right, title, and interest in Customer Data.

7. CONFIDENTIALITY
Each party agrees to maintain the confidentiality of the other party's Confidential Information for a period of five (5) years following disclosure.

8. INDEMNIFICATION
8.1 Provider Indemnification: Provider shall indemnify, defend, and hold harmless Customer from any claims arising from Provider's breach of this Agreement or infringement of third-party intellectual property rights.
8.2 Limitation: PROVIDER'S TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID BY CUSTOMER IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.

9. NON-COMPETE
Customer agrees that during the Term and for a period of two (2) years thereafter, Customer shall not directly or indirectly develop, market, or sell any product that competes with the Software.

10. MOST FAVORED CUSTOMER
Provider represents that the pricing provided to Customer is at least as favorable as pricing offered to any other customer of similar size and scope. If Provider offers more favorable terms to another customer, Customer shall be entitled to receive such terms.

11. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.
"""
    ),
    MockContract(
        id="contract-002",
        name="Executive Employment Agreement - John Smith",
        contract_type=ContractType.EMPLOYMENT,
        counterparty="John Smith (CEO)",
        effective_date="2022-03-01",
        expiration_date=None,
        value=850000.0,
        content="""
EXECUTIVE EMPLOYMENT AGREEMENT

This Executive Employment Agreement ("Agreement") is made effective as of March 1, 2022 ("Effective Date"), by and between TechCo Inc. ("Company") and John Smith ("Executive").

1. POSITION AND DUTIES
Executive is employed as Chief Executive Officer and shall report to the Board of Directors.

2. COMPENSATION
2.1 Base Salary: $500,000 annually, subject to annual review.
2.2 Annual Bonus: Target bonus of 70% of base salary, based on achievement of performance metrics.
2.3 Equity: Executive shall receive stock options for 500,000 shares, vesting over four (4) years with a one-year cliff.

3. BENEFITS
Executive shall be entitled to participate in all employee benefit plans, four (4) weeks paid vacation, and company-provided health insurance.

4. TERM
This Agreement shall continue until terminated by either party in accordance with Section 5.

5. TERMINATION
5.1 For Cause: Company may terminate Executive's employment for Cause, which includes:
    (a) Material breach of this Agreement
    (b) Conviction of a felony
    (c) Gross negligence or willful misconduct
    (d) Failure to perform duties after written notice

5.2 Without Cause: Company may terminate Executive without Cause upon thirty (30) days written notice.

5.3 Severance: Upon termination without Cause or resignation for Good Reason, Executive shall receive:
    (a) Eighteen (18) months of base salary continuation
    (b) Pro-rata bonus for the year of termination
    (c) Eighteen (18) months of COBRA premium payments
    (d) Immediate vesting of all unvested equity awards

6. CHANGE OF CONTROL
6.1 Definition: "Change of Control" means any transaction resulting in a change in ownership of more than 50% of the Company's voting securities or substantially all assets.

6.2 DOUBLE TRIGGER ACCELERATION: Upon a Change of Control followed by termination of Executive's employment without Cause or resignation for Good Reason within twenty-four (24) months, all unvested equity shall immediately vest ("Double Trigger").

6.3 ENHANCED SEVERANCE: In connection with a Change of Control termination, Executive shall receive:
    (a) Twenty-four (24) months of base salary (in lieu of standard severance)
    (b) Two (2) times target bonus
    (c) Twenty-four (24) months of COBRA premium payments
    (d) Full acceleration of all equity awards

6.4 GOLDEN PARACHUTE GROSS-UP: If any payment to Executive under this Agreement constitutes an "excess parachute payment" under Section 280G of the Internal Revenue Code, Company shall pay Executive an additional amount to cover any excise tax imposed.

7. NON-COMPETITION
7.1 During Employment: Executive shall not engage in any business competing with Company.
7.2 Post-Employment: For a period of twenty-four (24) months following termination, Executive shall not:
    (a) Engage in Competitive Activity within any geographic area where Company conducts business
    (b) Solicit any Company employee or customer
    (c) Use or disclose any Confidential Information

8. NON-SOLICITATION
For a period of twenty-four (24) months following termination, Executive shall not solicit, recruit, or hire any employee of the Company.

9. CONFIDENTIALITY
Executive shall maintain the confidentiality of all Company trade secrets and confidential information indefinitely.

10. INVENTION ASSIGNMENT
All inventions, discoveries, and works created by Executive during employment shall be the sole property of Company.

11. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.
"""
    ),
    MockContract(
        id="contract-003",
        name="Commercial Lease - Headquarters",
        contract_type=ContractType.LEASE,
        counterparty="Metropolitan Properties LLC",
        effective_date="2021-06-01",
        expiration_date="2031-05-31",
        value=1800000.0,
        content="""
COMMERCIAL LEASE AGREEMENT

This Commercial Lease Agreement ("Lease") is entered into as of June 1, 2021, by and between Metropolitan Properties LLC ("Landlord") and TechCo Inc. ("Tenant").

1. PREMISES
Landlord leases to Tenant approximately 45,000 square feet of office space located at 100 Tech Center Drive, San Francisco, CA 94105 ("Premises").

2. TERM
2.1 Initial Term: Ten (10) years commencing June 1, 2021.
2.2 Renewal Options: Two (2) consecutive five (5) year renewal options upon 180 days written notice.

3. RENT
3.1 Base Rent: $150,000 per month ($40 per square foot annually).
3.2 Annual Escalation: Base rent shall increase by 3% annually.
3.3 Operating Expenses: Tenant shall pay its proportionate share of operating expenses exceeding base year 2021.

4. SECURITY DEPOSIT
Tenant shall provide a security deposit of $900,000 (six months' rent).

5. USE
Premises shall be used for general office purposes, software development, and related business activities.

6. ALTERATIONS
Tenant may make alterations with Landlord's prior written consent, which shall not be unreasonably withheld for non-structural alterations costing less than $100,000.

7. ASSIGNMENT AND SUBLETTING
7.1 Consent Required: Tenant may not assign this Lease or sublet the Premises without Landlord's prior written consent.
7.2 CHANGE OF CONTROL RESTRICTION: Any Change of Control of Tenant shall be deemed an assignment requiring Landlord's consent. "Change of Control" means any merger, consolidation, or transfer of more than 50% of Tenant's ownership interests.
7.3 Landlord Recapture Right: Upon request to assign or sublet, Landlord may elect to terminate this Lease and recapture the Premises upon 90 days notice.
7.4 Excess Rent: Tenant shall pay Landlord 50% of any rent received in excess of Rent due under this Lease.

8. INSURANCE
Tenant shall maintain commercial general liability insurance of at least $5,000,000 per occurrence.

9. DEFAULT
9.1 Events of Default include: (a) failure to pay rent within 10 days of due date; (b) breach of any covenant; (c) bankruptcy or insolvency.
9.2 Remedies: Upon default, Landlord may terminate this Lease and seek damages including future rent and costs.

10. EARLY TERMINATION
10.1 Tenant Option: Tenant may terminate this Lease after year five (5) upon payment of an early termination fee equal to twelve (12) months' rent.
10.2 Notice: Tenant must provide at least 12 months written notice of intent to terminate.

11. PERSONAL GUARANTEE
The CEO of Tenant personally guarantees all obligations under this Lease for the first three (3) years of the Term.

12. GOVERNING LAW
This Lease shall be governed by the laws of the State of California.
"""
    ),
    MockContract(
        id="contract-004",
        name="IP License Agreement - PatentCo",
        contract_type=ContractType.IP_LICENSE,
        counterparty="PatentCo Holdings",
        effective_date="2022-09-01",
        expiration_date="2027-08-31",
        value=500000.0,
        content="""
INTELLECTUAL PROPERTY LICENSE AGREEMENT

This Intellectual Property License Agreement ("Agreement") is entered into as of September 1, 2022, by and between PatentCo Holdings ("Licensor") and TechCo Inc. ("Licensee").

1. LICENSED PATENTS
Licensor grants Licensee a non-exclusive license to the patents listed in Exhibit A ("Licensed Patents").

2. LICENSED FIELD
License is limited to enterprise software applications in the financial services and healthcare industries ("Licensed Field").

3. FEES
3.1 Upfront Fee: $250,000 upon execution.
3.2 Annual Royalty: 2% of Net Revenue from products using Licensed Patents, minimum $250,000 annually.
3.3 Royalty Reports: Quarterly reports due within 45 days of quarter end.

4. TERM
Five (5) year initial term with automatic renewal for successive one (1) year periods unless terminated.

5. SUBLICENSING
5.1 SUBLICENSE RESTRICTIONS: Licensee may grant sublicenses only with Licensor's prior written consent.
5.2 Sublicense terms must be consistent with this Agreement.
5.3 Licensee remains primarily liable for sublicensee compliance.

6. CHANGE OF CONTROL
6.1 LICENSOR TERMINATION RIGHT: Upon a Change of Control of Licensee to a Competitor (as defined in Exhibit B), Licensor may terminate this Agreement upon 90 days notice.
6.2 Increased Royalty: Upon Change of Control to a non-Competitor, royalty rate shall increase to 3% of Net Revenue.

7. IMPROVEMENTS
7.1 Licensee Improvements: Licensee grants Licensor a non-exclusive, royalty-free license to any improvements to the Licensed Patents.
7.2 Grant-Back: This grant-back shall survive termination of this Agreement.

8. AUDIT RIGHTS
Licensor may audit Licensee's records once per year upon 30 days notice. If audit reveals underpayment exceeding 5%, Licensee shall pay audit costs.

9. WARRANTY DISCLAIMER
LICENSED PATENTS ARE PROVIDED "AS IS." LICENSOR MAKES NO WARRANTY OF MERCHANTABILITY, FITNESS FOR PARTICULAR PURPOSE, OR NON-INFRINGEMENT.

10. INDEMNIFICATION
Licensee shall indemnify Licensor against claims arising from Licensee's use of Licensed Patents outside the Licensed Field.

11. LIMITATION OF LIABILITY
LICENSOR'S TOTAL LIABILITY SHALL NOT EXCEED FEES PAID IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.

12. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.
"""
    ),
    MockContract(
        id="contract-005",
        name="Credit Agreement - First National Bank",
        contract_type=ContractType.LOAN,
        counterparty="First National Bank",
        effective_date="2023-03-15",
        expiration_date="2028-03-14",
        value=25000000.0,
        content="""
CREDIT AGREEMENT

This Credit Agreement ("Agreement") is entered into as of March 15, 2023, by and between First National Bank ("Lender") and TechCo Inc. ("Borrower").

1. CREDIT FACILITY
Lender commits to provide Borrower a revolving credit facility of up to $25,000,000 ("Commitment").

2. INTEREST
2.1 Interest Rate: SOFR plus 2.50% per annum.
2.2 Default Rate: SOFR plus 5.50% per annum.

3. FEES
3.1 Commitment Fee: 0.375% per annum on unused Commitment.
3.2 Arrangement Fee: $125,000 upon closing.

4. TERM
Five (5) years from the Effective Date.

5. FINANCIAL COVENANTS
Borrower shall maintain:
5.1 Minimum Liquidity: Cash and cash equivalents of at least $5,000,000.
5.2 Maximum Leverage Ratio: Total Debt to EBITDA not exceeding 3.0:1.0.
5.3 Minimum Interest Coverage: EBITDA to Interest Expense of at least 3.0:1.0.
5.4 Revenue Covenant: Minimum annual revenue of $50,000,000.

6. CHANGE OF CONTROL
6.1 DEFINITION: "Change of Control" means (a) acquisition of 35% or more of voting securities by any person or group; (b) change in majority of Board of Directors; (c) sale of all or substantially all assets.

6.2 MANDATORY PREPAYMENT: Upon Change of Control, all outstanding principal and accrued interest shall become immediately due and payable.

6.3 NOTICE: Borrower shall provide Lender with at least 30 days prior written notice of any anticipated Change of Control.

7. NEGATIVE COVENANTS
Borrower shall not, without Lender's prior written consent:
7.1 Incur additional indebtedness exceeding $1,000,000
7.2 Create liens on any assets
7.3 Make acquisitions exceeding $5,000,000
7.4 Pay dividends exceeding 50% of net income
7.5 Dispose of assets exceeding $2,000,000

8. EVENTS OF DEFAULT
8.1 Payment default
8.2 Covenant breach
8.3 Cross-default on debt exceeding $500,000
8.4 Material adverse change
8.5 Change of Control without prepayment

9. REMEDIES
Upon Event of Default, Lender may:
9.1 Terminate Commitment
9.2 Accelerate all amounts due
9.3 Exercise all rights under security documents

10. SECURITY
This Agreement is secured by a first priority security interest in all assets of Borrower.

11. PERSONAL GUARANTEE
The CEO shall provide a personal guarantee limited to $5,000,000.

12. GOVERNING LAW
This Agreement shall be governed by the laws of the State of New York.
"""
    ),
]


def get_contract_by_id(contract_id: str) -> Optional[MockContract]:
    """Get a contract by its ID."""
    for contract in MOCK_CONTRACTS:
        if contract.id == contract_id:
            return contract
    return None


def get_contracts_by_type(contract_type: ContractType) -> list[MockContract]:
    """Get all contracts of a specific type."""
    return [c for c in MOCK_CONTRACTS if c.contract_type == contract_type]


def get_all_contracts() -> list[MockContract]:
    """Get all mock contracts."""
    return MOCK_CONTRACTS
