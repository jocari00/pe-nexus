# PE-Nexus Data Dictionary

## Overview

This document describes all data models, schemas, and their relationships in PE-Nexus.

## Core Entities

### MasterDeal

The central entity representing a private equity deal throughout its lifecycle.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| deal_id | UUID | Unique identifier | Yes |
| deal_name | string | Human-readable deal name | Yes |
| stage | DealStage | Current pipeline stage | Yes |
| target | TargetCompany | Target company details | Yes |
| financials | TracedFinancials[] | Financial data with provenance | No |

### DealStage Enum

| Value | Description |
|-------|-------------|
| SOURCING | Initial deal identification |
| TRIAGE | Initial screening and scoring |
| DILIGENCE | Due diligence phase |
| IC_REVIEW | Investment Committee review |
| CLOSING | Deal execution |
| PORTFOLIO | Post-close monitoring |
| EXITED | Deal completed |
| REJECTED | Deal declined |

### TracedValue

Every financial value includes full source traceability.

| Field | Type | Description |
|-------|------|-------------|
| value | Decimal | The numeric value |
| currency | Currency | USD, EUR, GBP |
| source | SourceReference | Document source |
| extraction_confidence | float | Model confidence (0-1) |

### SourceReference

Links extracted values to their source documents.

| Field | Type | Description |
|-------|------|-------------|
| document_id | UUID | Source document |
| page_number | int | Page in document |
| bounding_box | BoundingBox | PDF coordinates |
| text_snippet | string | Relevant text context |

### BoundingBox

PDF coordinate system for precise location tracking.

| Field | Type | Description |
|-------|------|-------------|
| x0 | float | Left coordinate |
| y0 | float | Top coordinate |
| x1 | float | Right coordinate |
| y1 | float | Bottom coordinate |

### Currency Enum

| Value | ISO 4217 | Description |
|-------|----------|-------------|
| USD | USD | US Dollar |
| EUR | EUR | Euro |
| GBP | GBP | British Pound |

## Relationships

```
MasterDeal (1) --> (*) TracedDocument
MasterDeal (1) --> (*) TracedFinancials
TracedFinancials --> TracedValue --> SourceReference --> Document
```

## API Schemas

### DealCreate (Request)

| Field | Type | Required |
|-------|------|----------|
| deal_name | string | Yes |
| target_company_name | string | Yes |
| industry | string | No |
| description | string | No |

### DealResponse

| Field | Type | Description |
|-------|------|-------------|
| deal_id | UUID | Unique identifier |
| deal_name | string | Deal name |
| stage | DealStage | Current stage |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

## Standard Mappings

- **Currency**: ISO 4217
- **Industry codes**: NAICS, SIC
- **Financial metrics**: Aligned with GAAP/IFRS definitions

## Event Types

| Event | Description | Payload |
|-------|-------------|---------|
| DEAL_CREATED | New deal added | deal_id, deal_name |
| STAGE_CHANGED | Deal transitioned | deal_id, old_stage, new_stage |
| DOCUMENT_UPLOADED | Document added | deal_id, document_id |
| FINANCIAL_EXTRACTED | Financials parsed | deal_id, metrics |
