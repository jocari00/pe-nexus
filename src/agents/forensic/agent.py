"""Forensic Analyst Agent for financial document extraction and validation."""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from src.agents.base import AgentOutput, AgentState, BaseAgent
from src.core.traceability import TracedExtraction
from src.schemas.financials import (
    BoundingBox,
    Currency,
    SourceReference,
    TracedFinancials,
    TracedValue,
)

from .pdf_extractor import PDFExtractor
from .reconciler import FinancialReconciler

logger = logging.getLogger(__name__)

# Financial metrics to extract
FINANCIAL_LABELS = [
    "Revenue",
    "Total Revenue",
    "Net Revenue",
    "Gross Profit",
    "EBITDA",
    "Adjusted EBITDA",
    "EBIT",
    "Operating Income",
    "Net Income",
    "Total Assets",
    "Total Liabilities",
    "Total Equity",
    "Stockholders Equity",
    "Cash",
    "Cash and Equivalents",
    "Total Debt",
    "Long-term Debt",
    "Operating Cash Flow",
    "Cash from Operations",
    "Capital Expenditures",
    "CapEx",
    "Free Cash Flow",
]


class ForensicAnalystAgent(BaseAgent):
    """
    Forensic Analyst Agent for CIM and financial document processing.

    Capabilities:
    - PDF extraction with bounding box tracking
    - Financial statement parsing
    - Cross-statement reconciliation
    - LLM-enhanced extraction for complex documents
    - Full traceability for all extracted values
    """

    def __init__(self):
        super().__init__(
            name="ForensicAnalyst",
            description=(
                "Extracts and validates financial data from CIMs and other documents. "
                "Every extracted value is traced to its source with page numbers and "
                "bounding boxes for verification."
            ),
            max_iterations=5,
        )
        self.reconciler = FinancialReconciler()

    def get_system_prompt(self) -> str:
        return """You are the Forensic Analyst, a specialized AI agent for extracting
financial data from private equity deal documents.

Your responsibilities:
1. Extract financial metrics accurately from documents
2. Identify the correct fiscal year/period for each metric
3. Note any adjustments or non-GAAP measures
4. Flag inconsistencies between different parts of documents
5. Provide confidence scores for each extraction

When extracting financial data:
- Always specify the fiscal year and period (FY, Q1-Q4, LTM, etc.)
- Distinguish between GAAP and adjusted figures
- Note the currency and units (thousands, millions, etc.)
- Identify the source page for each metric

Output format for extractions:
{
    "fiscal_year": 2023,
    "fiscal_period": "FY",
    "metrics": {
        "revenue": {"value": 125000000, "confidence": 0.95, "page": 15, "notes": ""},
        "ebitda": {"value": 25000000, "confidence": 0.90, "page": 15, "notes": "Adjusted EBITDA"},
        ...
    },
    "adjustments": [
        {"description": "One-time restructuring", "amount": -2000000, "page": 18}
    ],
    "flags": ["Revenue recognition policy change in FY2022"]
}
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for financial extraction."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        input_data = state.get("input_data", {})
        file_path = input_data.get("file_path")
        document_id = input_data.get("document_id")

        if not file_path:
            state["errors"].append("No file_path provided in input_data")
            return state

        try:
            # Step 1: Extract raw data from PDF
            with PDFExtractor(file_path) as extractor:
                # Get document metadata
                metadata = extractor.get_metadata()
                state["output_data"]["document_metadata"] = metadata

                # Extract all text for LLM processing
                all_text = extractor.get_all_text()
                state["output_data"]["page_count"] = metadata["page_count"]

                # Extract tables
                tables = extractor.get_tables()
                state["output_data"]["tables_found"] = len(tables)

                # Extract labeled financial values
                labeled_values = extractor.extract_labeled_values(FINANCIAL_LABELS)

                # Convert to traced extractions
                extractions = []
                for label, numbers in labeled_values.items():
                    for num in numbers:
                        extraction = self._create_traced_extraction(
                            label=label,
                            value=num.value,
                            page_number=num.page_number,
                            bounding_box=num.bounding_box,
                            context=num.context,
                            document_id=document_id or str(uuid4()),
                            document_name=file_path.split("/")[-1],
                        )
                        extractions.append(extraction)

                state["extractions"] = [e.model_dump() for e in extractions]

            # Step 2: Use LLM for enhanced extraction if API key available
            if self._client and all_text:
                llm_extractions = self._llm_extract_financials(all_text, state)
                if llm_extractions:
                    state["output_data"]["llm_extractions"] = llm_extractions

            # Step 3: Build TracedFinancials from extractions
            financials = self._build_traced_financials(state, document_id, file_path)
            if financials:
                state["output_data"]["financials"] = financials.model_dump()

                # Step 4: Run reconciliation
                report = self.reconciler.reconcile(financials)
                state["output_data"]["reconciliation"] = {
                    "passed": report.overall_pass,
                    "passed_count": report.passed_count,
                    "failed_count": report.failed_count,
                    "notes": report.notes,
                }

                if not report.overall_pass:
                    state["requires_review"] = True

            state["steps_completed"].append("process")

        except FileNotFoundError as e:
            state["errors"].append(f"File not found: {e}")
        except Exception as e:
            logger.error(f"Extraction error: {e}", exc_info=True)
            state["errors"].append(f"Extraction failed: {str(e)}")

        return state

    def _create_traced_extraction(
        self,
        label: str,
        value: Decimal,
        page_number: int,
        bounding_box: Optional[BoundingBox],
        context: str,
        document_id: str,
        document_name: str,
    ) -> TracedExtraction:
        """Create a traced extraction with full provenance."""
        prompt = f"Extract {label} value from financial document"

        return self.traceability.create_extraction(
            value=float(value),
            value_type="decimal",
            confidence=0.85,  # Base confidence for regex extraction
            document_id=UUID(document_id) if isinstance(document_id, str) else document_id,
            document_name=document_name,
            page_number=page_number,
            text_snippet=context,
            extraction_prompt=prompt,
            bounding_box=bounding_box,
        )

    def _llm_extract_financials(
        self,
        text_pages: list,
        state: AgentState,
    ) -> Optional[dict]:
        """Use LLM to extract structured financial data."""
        # Combine first 20 pages of text (typical CIM summary section)
        combined_text = "\n\n".join([
            f"--- Page {t.page_number} ---\n{t.text}"
            for t in text_pages[:20]
        ])

        # Truncate if too long
        if len(combined_text) > 50000:
            combined_text = combined_text[:50000] + "\n[TRUNCATED]"

        prompt = f"""Analyze the following financial document and extract key metrics.

Document text:
{combined_text}

Extract the following information in JSON format:
1. Company name
2. Fiscal year(s) covered
3. Key financial metrics (revenue, EBITDA, net income, etc.)
4. Any EBITDA adjustments mentioned
5. Key risks or flags you notice

For each metric, provide:
- value (as a number, not string)
- confidence (0.0-1.0)
- page number where found
- any notes (e.g., "adjusted", "pro forma")

Respond ONLY with valid JSON."""

        try:
            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=4096,
            )

            # Extract JSON from response using helper method
            text_content = self.get_text_from_response(response)
            if text_content:
                # Try to parse JSON
                try:
                    # Find JSON in response
                    json_start = text_content.find('{')
                    json_end = text_content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = text_content[json_start:json_end]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning("Could not parse LLM response as JSON")

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")

        return None

    def _build_traced_financials(
        self,
        state: AgentState,
        document_id: Optional[str],
        file_path: str,
    ) -> Optional[TracedFinancials]:
        """Build TracedFinancials from extractions."""
        extractions = state.get("extractions", [])
        llm_data = state.get("output_data", {}).get("llm_extractions", {})

        if not extractions and not llm_data:
            return None

        # Determine fiscal year from LLM extraction or default
        fiscal_year = datetime.now().year
        if llm_data and "fiscal_year" in llm_data:
            try:
                fiscal_year = int(llm_data["fiscal_year"])
            except (ValueError, TypeError):
                pass

        doc_id = UUID(document_id) if document_id else uuid4()
        doc_name = file_path.split("/")[-1] if file_path else "unknown.pdf"

        def make_traced_value(
            value: Any,
            page: int = 1,
            confidence: float = 0.8,
        ) -> TracedValue:
            """Helper to create TracedValue."""
            return TracedValue(
                value=Decimal(str(value)),
                currency=Currency.USD,
                source=SourceReference(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=page,
                    text_snippet="",
                ),
                extraction_confidence=confidence,
            )

        # Build financials from best available data
        financials = TracedFinancials(
            fiscal_year=fiscal_year,
            fiscal_period="FY",
        )

        # Map labels to financials fields
        label_mapping = {
            "Revenue": "revenue",
            "Total Revenue": "revenue",
            "Net Revenue": "revenue",
            "Gross Profit": "gross_profit",
            "EBITDA": "ebitda",
            "Adjusted EBITDA": "ebitda",
            "EBIT": "ebit",
            "Operating Income": "ebit",
            "Net Income": "net_income",
            "Total Assets": "total_assets",
            "Total Liabilities": "total_liabilities",
            "Total Equity": "total_equity",
            "Stockholders Equity": "total_equity",
            "Cash": "cash",
            "Cash and Equivalents": "cash",
            "Total Debt": "total_debt",
            "Long-term Debt": "total_debt",
            "Operating Cash Flow": "operating_cash_flow",
            "Cash from Operations": "operating_cash_flow",
            "Capital Expenditures": "capex",
            "CapEx": "capex",
            "Free Cash Flow": "free_cash_flow",
        }

        # Process regex extractions
        for ext in extractions:
            source = ext.get("source", {})
            label = None

            # Try to determine label from extraction prompt
            prompt = ext.get("extraction_prompt", "")
            for lbl in label_mapping:
                if lbl.lower() in prompt.lower():
                    label = lbl
                    break

            if label and label in label_mapping:
                field_name = label_mapping[label]
                if getattr(financials, field_name) is None:
                    traced_val = TracedValue(
                        value=Decimal(str(ext["value"])),
                        currency=Currency.USD,
                        source=SourceReference(
                            document_id=doc_id,
                            document_name=doc_name,
                            page_number=source.get("page_number", 1),
                            text_snippet=source.get("text_snippet", ""),
                            bounding_box=BoundingBox(**source["bounding_box"])
                            if source.get("bounding_box") else None,
                        ),
                        extraction_confidence=ext.get("confidence", 0.8),
                    )
                    setattr(financials, field_name, traced_val)

        # Supplement with LLM extractions
        if llm_data and "metrics" in llm_data:
            metrics = llm_data["metrics"]
            for label, data in metrics.items():
                if not isinstance(data, dict):
                    continue

                field_name = label_mapping.get(label) or label.lower().replace(" ", "_")
                if hasattr(financials, field_name) and getattr(financials, field_name) is None:
                    value = data.get("value")
                    if value is not None:
                        traced_val = make_traced_value(
                            value=value,
                            page=data.get("page", 1),
                            confidence=data.get("confidence", 0.75),
                        )
                        setattr(financials, field_name, traced_val)

        # Update confidence scores in state
        confidence_scores = {}
        for field in ["revenue", "ebitda", "net_income", "total_assets"]:
            traced_val = getattr(financials, field, None)
            if traced_val:
                confidence_scores[field] = traced_val.extraction_confidence

        state["confidence_scores"] = confidence_scores

        return financials

    def _is_processing_complete(self, state: AgentState) -> bool:
        """Check if extraction is complete."""
        # Complete if we have extractions or errors
        return bool(state.get("extractions")) or bool(state.get("errors"))


# Convenience function to create agent
def create_forensic_analyst() -> ForensicAnalystAgent:
    """Create a ForensicAnalyst agent instance."""
    return ForensicAnalystAgent()
