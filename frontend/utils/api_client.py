"""API Client for PE-Nexus FastAPI backend."""

import httpx
from typing import Any, Optional
import streamlit as st


class APIClient:
    """Wrapper for FastAPI backend calls."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 60.0  # Long timeout for LLM operations

    def _get_client(self) -> httpx.Client:
        """Get a synchronous HTTP client."""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and errors."""
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code}",
                "detail": response.text,
            }

    # ==========================================================================
    # Health Check
    # ==========================================================================

    def health_check(self) -> dict:
        """Check if the backend is running."""
        try:
            with self._get_client() as client:
                response = client.get("/health")
                return self._handle_response(response)
        except httpx.ConnectError:
            return {"status": "offline", "error": "Cannot connect to backend"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_llm_status(self) -> dict:
        """Get current LLM provider status."""
        health = self.health_check()
        if health.get("status") == "offline":
            return {
                "provider": "none",
                "model": "N/A",
                "display_name": "Backend Offline",
                "available": False,
            }
        return {
            "provider": health.get("llm_provider", "none"),
            "model": health.get("llm_model", "none"),
            "display_name": health.get("llm_display_name", "None"),
            "available": health.get("llm_provider") not in [None, "none"],
        }

    # ==========================================================================
    # Intelligence Scout
    # ==========================================================================

    def scout_analyze(
        self,
        company_name: str,
        industry: str = "",
        sub_sector: str = "",
    ) -> dict:
        """Analyze a company for deal potential."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/scout/analyze-sync",
                    json={
                        "company_name": company_name,
                        "industry": industry,
                        "sub_sector": sub_sector,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scout_scan(
        self,
        industry: Optional[str] = None,
        limit: int = 10,
        min_score: float = 3.5,
    ) -> dict:
        """Scan an industry for opportunities."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/scout/scan-sync",
                    json={
                        "industry": industry,
                        "limit": limit,
                        "min_score": min_score,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scout_signals(
        self,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> dict:
        """Get market signals."""
        try:
            with self._get_client() as client:
                params = {}
                if company_name:
                    params["company_name"] = company_name
                if industry:
                    params["industry"] = industry
                response = client.get("/agents/scout/signals", params=params)
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # Relationship Navigator
    # ==========================================================================

    def navigator_find_path(
        self,
        from_person: str,
        to_person: str,
        max_hops: int = 3,
    ) -> dict:
        """Find connection path between two people."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/navigator/find-path-sync",
                    json={
                        "from_person": from_person,
                        "to_person": to_person,
                        "max_hops": max_hops,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def navigator_suggest_intro(
        self,
        from_person: str,
        to_person: str,
        context: str = "",
    ) -> dict:
        """Get introduction suggestion with draft."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/navigator/suggest-intro-sync",
                    json={
                        "from_person": from_person,
                        "to_person": to_person,
                        "context": context,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def navigator_map_network(self, person: str, depth: int = 2) -> dict:
        """Map network around a person."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/navigator/map-network-sync",
                    json={"person": person, "depth": depth},
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def navigator_contacts(
        self,
        filter_type: str = "all",
        company: Optional[str] = None,
    ) -> dict:
        """List contacts in the network."""
        try:
            with self._get_client() as client:
                params = {"filter": filter_type}
                if company:
                    params["company"] = company
                response = client.get("/agents/navigator/contacts", params=params)
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # Legal Guardian
    # ==========================================================================

    def guardian_analyze(
        self,
        contract_id: Optional[str] = None,
        contract_text: Optional[str] = None,
        contract_name: str = "Unknown",
        contract_type: str = "unknown",
        counterparty: str = "Unknown",
    ) -> dict:
        """Analyze a contract for legal risks."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/guardian/analyze-sync",
                    json={
                        "contract_id": contract_id,
                        "contract_text": contract_text,
                        "contract_name": contract_name,
                        "contract_type": contract_type,
                        "counterparty": counterparty,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def guardian_analyze_all(self, contract_type: Optional[str] = None) -> dict:
        """Analyze all contracts."""
        try:
            with self._get_client() as client:
                params = {}
                if contract_type:
                    params["contract_type"] = contract_type
                response = client.post(
                    "/agents/guardian/analyze-all-sync", params=params
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def guardian_check_clause(self, clause_type: str) -> dict:
        """Check for specific clause type."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/guardian/check-clause-sync",
                    json={"clause_type": clause_type},
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def guardian_contracts(self) -> dict:
        """List all contracts."""
        try:
            with self._get_client() as client:
                response = client.get("/agents/guardian/contracts")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # Quant Strategist
    # ==========================================================================

    def strategist_lbo(
        self,
        ltm_revenue: float,
        ltm_ebitda: float,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        holding_period: int = 5,
        leverage: float = 4.0,
        revenue_growth: float = 0.05,
        net_debt: float = 0.0,
        interest_rate: float = 0.08,
        tax_rate: float = 0.25,
    ) -> dict:
        """Build an LBO model."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/strategist/lbo-sync",
                    json={
                        "ltm_revenue": ltm_revenue,
                        "ltm_ebitda": ltm_ebitda,
                        "entry_multiple": entry_multiple,
                        "exit_multiple": exit_multiple,
                        "holding_period": holding_period,
                        "leverage": leverage,
                        "revenue_growth": revenue_growth,
                        "net_debt": net_debt,
                        "interest_rate": interest_rate,
                        "tax_rate": tax_rate,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def strategist_analyze(
        self,
        company_name: str,
        ltm_revenue: float,
        ltm_ebitda: float,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        holding_period: int = 5,
        leverage: float = 4.0,
        revenue_growth: float = 0.05,
    ) -> dict:
        """Full LBO analysis with commentary."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/strategist/analyze-sync",
                    json={
                        "company_name": company_name,
                        "ltm_revenue": ltm_revenue,
                        "ltm_ebitda": ltm_ebitda,
                        "entry_multiple": entry_multiple,
                        "exit_multiple": exit_multiple,
                        "holding_period": holding_period,
                        "leverage": leverage,
                        "revenue_growth": revenue_growth,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def strategist_sensitivity(
        self,
        ltm_revenue: float,
        ltm_ebitda: float,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        sensitivity_type: str = "entry_exit",
        metric: str = "irr",
    ) -> dict:
        """Generate sensitivity tables."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/strategist/sensitivity-sync",
                    json={
                        "ltm_revenue": ltm_revenue,
                        "ltm_ebitda": ltm_ebitda,
                        "entry_multiple": entry_multiple,
                        "exit_multiple": exit_multiple,
                        "sensitivity_type": sensitivity_type,
                        "metric": metric,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # Adversarial IC
    # ==========================================================================

    def ic_debate(
        self,
        company_name: str,
        industry: str = "Technology",
        revenue: float = 100.0,
        ebitda: float = 20.0,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        irr: str = "20%",
        moic: str = "2.5x",
        strengths: list = None,
        growth_rate: str = "5",
    ) -> dict:
        """Run full IC debate."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/ic/debate-sync",
                    json={
                        "deal_context": {
                            "company_name": company_name,
                            "industry": industry,
                            "revenue": revenue,
                            "ebitda": ebitda,
                            "entry_multiple": entry_multiple,
                            "exit_multiple": exit_multiple,
                            "irr": irr,
                            "moic": moic,
                            "strengths": strengths or [],
                            "growth_rate": growth_rate,
                        }
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def ic_memo(
        self,
        company_name: str,
        industry: str = "Technology",
        revenue: float = 100.0,
        ebitda: float = 20.0,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        irr: str = "20%",
        moic: str = "2.5x",
    ) -> dict:
        """Generate investment memo only."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/ic/memo-sync",
                    json={
                        "deal_context": {
                            "company_name": company_name,
                            "industry": industry,
                            "revenue": revenue,
                            "ebitda": ebitda,
                            "entry_multiple": entry_multiple,
                            "exit_multiple": exit_multiple,
                            "irr": irr,
                            "moic": moic,
                        }
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def ic_bear(
        self,
        company_name: str,
        industry: str = "Technology",
        revenue: float = 100.0,
        ebitda: float = 20.0,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        irr: str = "20%",
        moic: str = "2.5x",
    ) -> dict:
        """Generate bear case only."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/ic/bear-sync",
                    json={
                        "deal_context": {
                            "company_name": company_name,
                            "industry": industry,
                            "revenue": revenue,
                            "ebitda": ebitda,
                            "entry_multiple": entry_multiple,
                            "exit_multiple": exit_multiple,
                            "irr": irr,
                            "moic": moic,
                        }
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # Value Creation Monitor
    # ==========================================================================

    def monitor_dashboard(self) -> dict:
        """Get portfolio dashboard."""
        try:
            with self._get_client() as client:
                response = client.get("/agents/monitor/dashboard")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def monitor_companies(
        self,
        status: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> dict:
        """List portfolio companies."""
        try:
            with self._get_client() as client:
                params = {}
                if status:
                    params["status"] = status
                if industry:
                    params["industry"] = industry
                response = client.get("/agents/monitor/companies", params=params)
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def monitor_company(self, company_id: str) -> dict:
        """Get company details."""
        try:
            with self._get_client() as client:
                response = client.get(f"/agents/monitor/company/{company_id}")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def monitor_analyze(self, company_id: str, period: str = "quarterly") -> dict:
        """Analyze company KPIs."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/monitor/analyze-sync",
                    json={"company_id": company_id, "period": period},
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def monitor_alerts(
        self,
        severity: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> dict:
        """Get portfolio alerts."""
        try:
            with self._get_client() as client:
                params = {}
                if severity:
                    params["severity"] = severity
                if company_id:
                    params["company_id"] = company_id
                response = client.get("/agents/monitor/alerts", params=params)
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def monitor_report(
        self,
        quarter: int = 4,
        year: int = 2025,
        fund_name: str = "PE-Nexus Fund I",
    ) -> dict:
        """Generate LP report."""
        try:
            with self._get_client() as client:
                response = client.post(
                    "/agents/monitor/report-sync",
                    json={
                        "quarter": quarter,
                        "year": year,
                        "fund_name": fund_name,
                    },
                )
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}


    # ==========================================================================
    # Synthesis (Deal Command Center)
    # ==========================================================================

    def synthesis_leaderboard(
        self,
        min_score: int = 0,
        limit: int = 20,
        industry: str = None,
        status: str = None,
    ) -> dict:
        """Get the high-conviction leaderboard for the Deal Command Center."""
        try:
            with self._get_client() as client:
                params = {"min_score": min_score, "limit": limit}
                if industry:
                    params["industry"] = industry
                if status:
                    params["status"] = status
                response = client.get("/synthesis/leaderboard", params=params)
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def synthesis_company(self, company_id: str) -> dict:
        """Get unified intelligence view for a company."""
        try:
            with self._get_client() as client:
                response = client.get(f"/synthesis/company/{company_id}")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def synthesis_company_summary(self, company_id: str) -> dict:
        """Get quick summary for a company card."""
        try:
            with self._get_client() as client:
                response = client.get(f"/synthesis/company/{company_id}/summary")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # FAIR Compliance
    # ==========================================================================

    def fair_metadata(self) -> dict:
        """Get FAIR metadata in JSON-LD format."""
        try:
            with self._get_client() as client:
                response = client.get("/fair/metadata")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fair_principles(self) -> dict:
        """Get detailed FAIR principles assessment."""
        try:
            with self._get_client() as client:
                response = client.get("/fair/principles")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fair_score(self) -> dict:
        """Get FAIR compliance score summary."""
        try:
            with self._get_client() as client:
                response = client.get("/fair/score")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fair_files(self) -> dict:
        """Get list of FAIR-related files."""
        try:
            with self._get_client() as client:
                response = client.get("/fair/files")
                return self._handle_response(response)
        except Exception as e:
            return {"success": False, "error": str(e)}


@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()
