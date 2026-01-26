"""RelationshipNavigator Agent - Finds warm introduction paths through professional networks.

This agent uses graph traversal algorithms to find connection paths between
people, calculates path strength, and generates introduction drafts.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from src.agents.base import AgentOutput, AgentState, BaseAgent

from .mock_data import (
    MOCK_PEOPLE,
    MOCK_RELATIONSHIPS,
    RelationshipType,
    get_firm_partner_ids,
    get_mock_person_by_id,
    get_mock_person_by_name,
    get_target_executive_ids,
)
from .path_finder import ConnectionPath, NetworkGraph, PathFinder, PathNode

logger = logging.getLogger(__name__)


class RelationshipNavigatorAgent(BaseAgent):
    """
    Autonomous agent for finding warm introduction paths through professional networks.

    Capabilities:
    - Finds connection paths between people (up to N hops)
    - Calculates path strength based on relationship types
    - Generates personalized introduction request drafts
    - Maps network neighborhoods for visualization

    Workflow:
    1. Accept source and target person identifiers
    2. Traverse relationship graph using recursive CTEs
    3. Score paths by relationship strength and hop count
    4. Generate LLM-enhanced introduction drafts
    5. Return ranked paths with actionable next steps
    """

    def __init__(self, db_session=None):
        """
        Initialize the RelationshipNavigator agent.

        Args:
            db_session: Optional database session. If None, uses mock data.
        """
        super().__init__(
            name="RelationshipNavigator",
            description="Finds warm introduction paths through professional networks",
            max_iterations=3,
        )

        self.path_finder = PathFinder(db_session=db_session)

    def get_system_prompt(self) -> str:
        """System prompt for LLM interactions."""
        return """You are a Relationship Intelligence Analyst at a private equity firm.
Your role is to help identify the best introduction paths to target executives and craft
warm introduction requests.

When analyzing connection paths, you should:
1. Evaluate the strength and quality of each relationship in the path
2. Consider the context (how they know each other, shared experiences)
3. Draft professional, personalized introduction requests
4. Suggest talking points based on shared backgrounds

For introduction drafts:
- Keep the tone professional but warm
- Reference specific shared experiences or connections
- Be concise but include relevant context
- Suggest a clear ask (meeting, call, coffee, etc.)

Format introduction drafts as:
Subject: [Suggested subject line]
Body: [Email body]
Talking Points: [2-3 bullet points for the introducer]
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for the Navigator agent."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            mode = input_data.get("mode", "find_path")

            if mode == "find_path":
                result = self._find_path(input_data, state)
            elif mode == "map_network":
                result = self._map_network(input_data, state)
            elif mode == "suggest_intro":
                result = self._suggest_introduction(input_data, state)
            elif mode == "list_contacts":
                result = self._list_contacts(input_data, state)
            else:
                state["errors"].append(f"Unknown mode: {mode}")
                return state

            state["output_data"] = result
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _find_path(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Find connection paths between two people."""
        from_person = input_data.get("from_person")
        to_person = input_data.get("to_person")
        max_hops = input_data.get("max_hops", 3)

        if not from_person or not to_person:
            state["errors"].append("Both from_person and to_person are required")
            return {}

        # Resolve person identifiers (could be ID, name, or company+title)
        from_id = self._resolve_person_id(from_person)
        to_id = self._resolve_person_id(to_person)

        if not from_id:
            state["errors"].append(f"Could not find person: {from_person}")
            return {}
        if not to_id:
            state["errors"].append(f"Could not find person: {to_person}")
            return {}

        # Use synchronous path finding (mock data doesn't need async)
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            paths = loop.run_until_complete(
                self.path_finder.find_paths(from_id, to_id, max_hops)
            )
        finally:
            loop.close()

        if not paths:
            return {
                "mode": "find_path",
                "from_person": from_person,
                "to_person": to_person,
                "paths_found": 0,
                "paths": [],
                "message": f"No connection path found within {max_hops} hops",
            }

        # Store extraction record for traceability
        extraction_record = {
            "type": "path_discovery",
            "from_person": from_person,
            "to_person": to_person,
            "paths_found": len(paths),
            "best_path_strength": paths[0].path_strength if paths else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # Calculate confidence based on path quality
        best_strength = paths[0].path_strength if paths else 0
        state["confidence_scores"]["path_discovery"] = min(0.95, 0.5 + best_strength * 0.5)

        return {
            "mode": "find_path",
            "from_person": from_person,
            "to_person": to_person,
            "paths_found": len(paths),
            "paths": [p.to_dict() for p in paths[:5]],  # Return top 5 paths
            "best_path": paths[0].to_dict() if paths else None,
        }

    def _map_network(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Map the network around a person."""
        person = input_data.get("person")
        depth = input_data.get("depth", 2)

        if not person:
            state["errors"].append("person is required for map_network mode")
            return {}

        person_id = self._resolve_person_id(person)
        if not person_id:
            state["errors"].append(f"Could not find person: {person}")
            return {}

        # Get network map
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            network = loop.run_until_complete(
                self.path_finder.get_network_map(person_id, depth)
            )
        finally:
            loop.close()

        # Store extraction record
        extraction_record = {
            "type": "network_map",
            "center_person": person,
            "depth": depth,
            "nodes_found": len(network.nodes),
            "edges_found": len(network.edges),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        return {
            "mode": "map_network",
            "person": person,
            "depth": depth,
            "network": network.to_dict(),
        }

    def _suggest_introduction(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Find best path and generate introduction draft."""
        from_person = input_data.get("from_person")
        to_person = input_data.get("to_person")
        context = input_data.get("context", "")

        if not from_person or not to_person:
            state["errors"].append("Both from_person and to_person are required")
            return {}

        # First find the best path
        from_id = self._resolve_person_id(from_person)
        to_id = self._resolve_person_id(to_person)

        if not from_id or not to_id:
            state["errors"].append("Could not resolve person identifiers")
            return {}

        import asyncio

        loop = asyncio.new_event_loop()
        try:
            paths = loop.run_until_complete(
                self.path_finder.find_paths(from_id, to_id, max_hops=3)
            )
        finally:
            loop.close()

        if not paths:
            return {
                "mode": "suggest_intro",
                "from_person": from_person,
                "to_person": to_person,
                "success": False,
                "message": "No connection path found",
            }

        best_path = paths[0]

        # Generate introduction draft using LLM if available
        intro_draft = self._generate_intro_draft(best_path, context)

        # Store extraction record
        extraction_record = {
            "type": "introduction_suggestion",
            "from_person": from_person,
            "to_person": to_person,
            "path_hops": best_path.total_hops,
            "path_strength": best_path.path_strength,
            "llm_enhanced": self._client is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)
        state["confidence_scores"]["introduction"] = min(0.90, 0.6 + best_path.path_strength * 0.3)

        return {
            "mode": "suggest_intro",
            "from_person": from_person,
            "to_person": to_person,
            "success": True,
            "best_path": best_path.to_dict(),
            "introduction_draft": intro_draft,
            "alternative_paths": [p.to_dict() for p in paths[1:3]],  # 2 alternatives
        }

    def _list_contacts(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """List contacts, optionally filtered by company or firm status."""
        filter_type = input_data.get("filter", "all")
        company = input_data.get("company")

        contacts = []
        for person in MOCK_PEOPLE:
            include = True

            if filter_type == "firm" and not person.is_firm_contact:
                include = False
            elif filter_type == "external" and person.is_firm_contact:
                include = False
            elif company and company.lower() not in person.company.lower():
                include = False

            if include:
                contacts.append({
                    "id": person.id,
                    "name": person.name,
                    "title": person.title,
                    "company": person.company,
                    "email": person.email,
                    "is_firm_contact": person.is_firm_contact,
                })

        return {
            "mode": "list_contacts",
            "filter": filter_type,
            "company": company,
            "contacts": contacts,
            "total_count": len(contacts),
        }

    def _resolve_person_id(self, identifier: str) -> Optional[str]:
        """
        Resolve a person identifier to their UUID.

        Accepts:
        - UUID string directly
        - Person name (partial match)
        - Company:Title format
        """
        # Check if it's already a UUID
        if len(identifier) == 36 and "-" in identifier:
            return identifier

        # Try name match
        person = get_mock_person_by_name(identifier)
        if person:
            return person.id

        # Try company:title format
        if ":" in identifier:
            company, title = identifier.split(":", 1)
            for p in MOCK_PEOPLE:
                if (
                    company.lower() in p.company.lower()
                    and title.lower() in p.title.lower()
                ):
                    return p.id

        return None

    def _generate_intro_draft(
        self, path: ConnectionPath, context: str = ""
    ) -> dict[str, Any]:
        """Generate introduction request draft."""
        # Build introduction context from path
        introducer = path.nodes[1] if len(path.nodes) > 2 else path.nodes[0]
        target = path.target_person
        source = path.source_person

        # Get relationship context
        intro_relationship = path.edges[0] if path.edges else None
        intro_context = intro_relationship.context if intro_relationship else ""

        # Try LLM enhancement if available
        if self._client is not None:
            try:
                return self._enhance_intro_with_llm(
                    source=source,
                    introducer=introducer,
                    target=target,
                    path=path,
                    relationship_context=intro_context,
                    additional_context=context,
                )
            except Exception as e:
                logger.warning(f"LLM intro generation failed: {e}")

        # Fallback to template-based generation
        return self._generate_template_intro(
            source=source,
            introducer=introducer,
            target=target,
            path=path,
            relationship_context=intro_context,
        )

    def _enhance_intro_with_llm(
        self,
        source: PathNode,
        introducer: PathNode,
        target: PathNode,
        path: ConnectionPath,
        relationship_context: str,
        additional_context: str,
    ) -> dict[str, Any]:
        """Use LLM to generate personalized introduction draft."""
        prompt = f"""Generate an introduction request for a private equity professional.

Requester: {source.name}, {source.title} at {source.company}
Introducer: {introducer.name}, {introducer.title} at {introducer.company}
Target: {target.name}, {target.title} at {target.company}

Connection Chain:
{chr(10).join(path.introduction_chain)}

How introducer knows target: {relationship_context}
Additional context: {additional_context or 'Exploring potential acquisition opportunity'}

Generate:
1. A subject line for the introduction request email
2. The email body to the introducer asking for the introduction
3. 3 talking points for the introducer to use

Format as JSON:
{{
    "subject": "Subject line",
    "body": "Email body text",
    "talking_points": ["point 1", "point 2", "point 3"],
    "best_approach": "Recommendation on best way to approach"
}}
"""

        response = self.call_llm(
            messages=[{"role": "user", "content": prompt}],
            system=self.get_system_prompt(),
            max_tokens=1024,
        )

        text = self.get_text_from_response(response)
        if text:
            # Extract JSON
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                intro_data = json.loads(text[json_start:json_end])
                intro_data["llm_generated"] = True
                intro_data["introducer"] = {
                    "name": introducer.name,
                    "title": introducer.title,
                    "company": introducer.company,
                    "email": introducer.email,
                }
                return intro_data

        # Fall back to template
        return self._generate_template_intro(
            source, introducer, target, path, relationship_context
        )

    def _generate_template_intro(
        self,
        source: PathNode,
        introducer: PathNode,
        target: PathNode,
        path: ConnectionPath,
        relationship_context: str,
    ) -> dict[str, Any]:
        """Generate template-based introduction draft."""
        subject = f"Introduction Request: {target.name} at {target.company}"

        body = f"""Hi {introducer.name.split()[0]},

I hope this email finds you well. I'm reaching out because I understand you have a connection with {target.name}, {target.title} at {target.company}.

At {source.company}, we're currently exploring opportunities in the enterprise software space and {target.company} has come up as a company we'd love to learn more about.

Given your relationship ({relationship_context or 'professional connection'}), I was hoping you might be open to making an introduction. I'd greatly appreciate even a brief call with {target.name.split()[0]} to learn more about their business and vision.

Please let me know if you'd be comfortable facilitating this connection, and I'm happy to provide any additional context that would be helpful.

Best regards,
{source.name}
{source.title}
{source.company}"""

        talking_points = [
            f"{source.name} is a {source.title} at {source.company}, a reputable PE firm",
            f"They're interested in learning about {target.company}'s business, not a hard sell",
            "A brief introductory call would be greatly appreciated",
        ]

        return {
            "subject": subject,
            "body": body,
            "talking_points": talking_points,
            "best_approach": f"Email {introducer.name} with the introduction request",
            "llm_generated": False,
            "introducer": {
                "name": introducer.name,
                "title": introducer.title,
                "company": introducer.company,
                "email": introducer.email,
            },
        }

    def _is_processing_complete(self, state: AgentState) -> bool:
        """Check if processing is complete."""
        return bool(state.get("output_data")) or bool(state.get("errors"))

    # Convenience methods for direct API usage

    async def find_path(
        self,
        from_person: str,
        to_person: str,
        max_hops: int = 3,
    ) -> AgentOutput:
        """
        Find connection paths between two people.

        Args:
            from_person: Source person (ID, name, or company:title)
            to_person: Target person (ID, name, or company:title)
            max_hops: Maximum hops to search (default 3)

        Returns:
            AgentOutput with found paths
        """
        input_data = {
            "mode": "find_path",
            "from_person": from_person,
            "to_person": to_person,
            "max_hops": max_hops,
        }
        return await self.run(input_data=input_data)

    async def map_network(
        self,
        person: str,
        depth: int = 2,
    ) -> AgentOutput:
        """
        Map the network around a person.

        Args:
            person: Center person (ID, name, or company:title)
            depth: How many hops to include (default 2)

        Returns:
            AgentOutput with network graph
        """
        input_data = {
            "mode": "map_network",
            "person": person,
            "depth": depth,
        }
        return await self.run(input_data=input_data)

    async def suggest_introduction(
        self,
        from_person: str,
        to_person: str,
        context: str = "",
    ) -> AgentOutput:
        """
        Find best path and generate introduction draft.

        Args:
            from_person: Source person (your firm contact)
            to_person: Target person to reach
            context: Additional context for the introduction

        Returns:
            AgentOutput with path and introduction draft
        """
        input_data = {
            "mode": "suggest_intro",
            "from_person": from_person,
            "to_person": to_person,
            "context": context,
        }
        return await self.run(input_data=input_data)

    async def list_contacts(
        self,
        filter_type: str = "all",
        company: Optional[str] = None,
    ) -> AgentOutput:
        """
        List available contacts.

        Args:
            filter_type: "all", "firm", or "external"
            company: Optional company name filter

        Returns:
            AgentOutput with contact list
        """
        input_data = {
            "mode": "list_contacts",
            "filter": filter_type,
            "company": company,
        }
        return await self.run(input_data=input_data)


def create_navigator(db_session=None) -> RelationshipNavigatorAgent:
    """Factory function to create a RelationshipNavigator agent."""
    return RelationshipNavigatorAgent(db_session=db_session)
