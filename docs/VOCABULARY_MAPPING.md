# Vocabulary Mapping

This document maps PE-Nexus internal vocabularies to standard ontologies and classifications.

## Currency (ISO 4217)

| Internal Value | ISO 4217 Code | Standard Name |
|----------------|---------------|---------------|
| USD | USD | US Dollar |
| EUR | EUR | Euro |
| GBP | GBP | British Pound |

## Industry Classification

PE-Nexus uses both NAICS and SIC codes for industry classification.

| Field | Standard | Reference |
|-------|----------|-----------|
| naics_code | NAICS 2022 | https://www.census.gov/naics/ |
| sic_code | SIC | https://www.osha.gov/data/sic-manual |

## Financial Metrics

| PE-Nexus Field | Definition | XBRL Equivalent |
|----------------|------------|-----------------|
| revenue | Total revenue | Revenues |
| ebitda | Earnings before interest, taxes, depreciation, amortization | N/A (calculated) |
| net_income | Net income after all expenses | NetIncomeLoss |
| total_assets | Sum of all assets | Assets |
| total_debt | Sum of all debt obligations | LongTermDebt + ShortTermBorrowings |
| gross_margin | Gross profit / Revenue | GrossProfit / Revenues |
| operating_margin | Operating income / Revenue | OperatingIncomeLoss / Revenues |

## Deal Stage Mapping

| PE-Nexus Stage | Industry Term | Description |
|----------------|---------------|-------------|
| SOURCING | Origination | Initial deal identification and screening |
| TRIAGE | Preliminary Review | Quick assessment of fit and potential |
| DILIGENCE | Due Diligence | Comprehensive investigation |
| IC_REVIEW | Investment Committee | Formal approval process |
| CLOSING | Execution | Legal and financial closing |
| PORTFOLIO | Post-Acquisition | Active ownership period |
| EXITED | Realization | Sale or IPO completed |
| REJECTED | Pass | Deal declined at any stage |

## Schema.org Mappings

For codemeta.json and structured data:

| PE-Nexus Concept | Schema.org Type |
|------------------|-----------------|
| Author | schema:Person |
| Software | schema:SoftwareSourceCode |
| License | schema:CreativeWork |
| Organization | schema:Organization |

## Document Types

| Internal Type | Description | Common Formats |
|---------------|-------------|----------------|
| CIM | Confidential Information Memorandum | PDF |
| FINANCIAL_STATEMENT | Audited financials | PDF, Excel |
| VDR_DOCUMENT | Virtual data room documents | Various |
| MODEL | Financial model | Excel |
| LEGAL | Legal documents | PDF, Word |

## Future Standards Consideration

- **XBRL**: Consider full XBRL taxonomy alignment for financial data
- **FIX Protocol**: For trade-related messaging
- **ILPA Standards**: For LP reporting templates
- **ESG Frameworks**: SASB, GRI for sustainability metrics
