"""Base Agent class with LangGraph integration for PE-Nexus agents."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional, TypedDict, Union
from uuid import UUID, uuid4

from langgraph.graph import END, StateGraph

from src.core.config import settings
from src.core.events import EventBus, get_event_bus
from src.core.traceability import TraceabilityEngine, get_traceability_engine
from src.schemas.events import EventType

logger = logging.getLogger(__name__)

# Lazy imports for LLM clients
_anthropic_client = None
_groq_client = None
_ollama_client = None


def get_anthropic_client():
    """Get or create Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def get_groq_client():
    """Get or create Groq client."""
    global _groq_client
    if _groq_client is None and settings.groq_api_key:
        from groq import Groq
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def get_ollama_client():
    """Get or create Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        try:
            import ollama
            _ollama_client = ollama
        except ImportError:
            logger.warning("Ollama package not installed")
    return _ollama_client


class AgentState(TypedDict, total=False):
    """Base state for all agents."""

    # Task context
    task_id: str
    deal_id: Optional[str]
    document_id: Optional[str]

    # Input/Output
    input_data: dict[str, Any]
    output_data: dict[str, Any]

    # Execution tracking
    current_step: str
    steps_completed: list[str]
    errors: list[str]

    # LLM interaction
    messages: list[dict[str, Any]]
    iterations: int
    max_iterations: int

    # Results
    extractions: list[dict[str, Any]]
    confidence_scores: dict[str, float]
    requires_review: bool


class AgentOutput:
    """Standard output format for agent execution."""

    def __init__(
        self,
        agent_name: str,
        task_id: str,
        success: bool,
        output_data: dict[str, Any],
        extractions: Optional[list] = None,
        errors: Optional[list[str]] = None,
        duration_seconds: Optional[float] = None,
        requires_review: bool = False,
    ):
        self.agent_name = agent_name
        self.task_id = task_id
        self.success = success
        self.output_data = output_data
        self.extractions = extractions or []
        self.errors = errors or []
        self.duration_seconds = duration_seconds
        self.requires_review = requires_review
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "success": self.success,
            "output_data": self.output_data,
            "extractions": self.extractions,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
            "requires_review": self.requires_review,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """
    Abstract base class for all PE-Nexus agents.

    Provides:
    - LangGraph state machine integration
    - Multi-provider LLM access (Claude, Groq/Llama, Ollama)
    - Event bus integration
    - Traceability engine access
    - Standard execution patterns
    """

    def __init__(
        self,
        name: str,
        description: str,
        model: Optional[str] = None,
        max_iterations: int = 10,
    ):
        self.name = name
        self.description = description
        self.max_iterations = max_iterations

        # Get active LLM provider from settings
        self._llm_provider = settings.active_llm_provider
        self.model = model or settings.active_model_name

        # Initialize the appropriate client based on provider
        self._client = None
        if self._llm_provider == "anthropic":
            self._client = get_anthropic_client()
        elif self._llm_provider == "groq":
            self._client = get_groq_client()
        elif self._llm_provider == "ollama":
            self._client = get_ollama_client()

        logger.info(
            f"{name}: Using LLM provider '{self._llm_provider or 'none'}' "
            f"with model '{self.model}'"
        )

        # Services
        self._event_bus: Optional[EventBus] = None
        self._traceability: Optional[TraceabilityEngine] = None

        # Build the LangGraph workflow
        self._graph = self._build_graph()
        self._compiled_graph = self._graph.compile()

    @property
    def has_llm(self) -> bool:
        """Check if an LLM client is available."""
        return self._client is not None

    @property
    def llm_provider_name(self) -> str:
        """Get human-readable LLM provider name."""
        return settings.llm_display_name

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus instance."""
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    @property
    def traceability(self) -> TraceabilityEngine:
        """Get the traceability engine instance."""
        if self._traceability is None:
            self._traceability = get_traceability_engine()
        return self._traceability

    @property
    def client(self):
        """Get the LLM client (for backwards compatibility)."""
        if self._client is None:
            raise ValueError(
                "No LLM client initialized. "
                "Set GROQ_API_KEY (free) or ANTHROPIC_API_KEY in .env file."
            )
        return self._client

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine for this agent.

        Override in subclasses to customize the workflow.
        """
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("initialize", self._initialize_node)
        graph.add_node("process", self._process_node)
        graph.add_node("validate", self._validate_node)
        graph.add_node("finalize", self._finalize_node)

        # Set entry point
        graph.set_entry_point("initialize")

        # Add edges
        graph.add_edge("initialize", "process")
        graph.add_conditional_edges(
            "process",
            self._should_continue,
            {
                "continue": "process",
                "validate": "validate",
                "error": "finalize",
            },
        )
        graph.add_edge("validate", "finalize")
        graph.add_edge("finalize", END)

        return graph

    def _initialize_node(self, state: AgentState) -> AgentState:
        """Initialize the agent state."""
        state["task_id"] = state.get("task_id", str(uuid4()))
        state["current_step"] = "initialize"
        state["steps_completed"] = []
        state["errors"] = []
        state["iterations"] = 0
        state["max_iterations"] = self.max_iterations
        state["extractions"] = []
        state["confidence_scores"] = {}
        state["requires_review"] = False
        state["output_data"] = {}

        logger.info(f"{self.name}: Initialized task {state['task_id']}")
        return state

    @abstractmethod
    def _process_node(self, state: AgentState) -> AgentState:
        """
        Main processing logic for the agent.

        Must be implemented by subclasses.
        """
        pass

    def _validate_node(self, state: AgentState) -> AgentState:
        """Validate agent output before finalization."""
        state["current_step"] = "validate"

        # Check for low confidence extractions
        for field, confidence in state.get("confidence_scores", {}).items():
            if confidence < settings.pdf_extraction_confidence_threshold:
                state["requires_review"] = True
                logger.warning(
                    f"{self.name}: Low confidence ({confidence:.2f}) for {field}"
                )

        state["steps_completed"].append("validate")
        return state

    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize agent execution."""
        state["current_step"] = "finalize"
        state["steps_completed"].append("finalize")

        logger.info(
            f"{self.name}: Finalized task {state['task_id']} "
            f"with {len(state.get('errors', []))} errors"
        )
        return state

    def _should_continue(self, state: AgentState) -> str:
        """Determine if processing should continue."""
        iterations = state.get("iterations", 0)
        max_iterations = state.get("max_iterations", self.max_iterations)
        errors = state.get("errors", [])

        if errors:
            return "error"

        if iterations >= max_iterations:
            logger.warning(f"{self.name}: Max iterations reached")
            return "validate"

        # Check if processing is complete (to be overridden)
        if self._is_processing_complete(state):
            return "validate"

        return "continue"

    def _is_processing_complete(self, state: AgentState) -> bool:
        """
        Check if processing is complete.

        Override in subclasses for custom completion logic.
        """
        return True

    async def run(
        self,
        input_data: dict[str, Any],
        deal_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
    ) -> AgentOutput:
        """
        Execute the agent workflow.

        Args:
            input_data: Input data for the agent
            deal_id: Optional deal context
            document_id: Optional document context

        Returns:
            AgentOutput with results
        """
        start_time = datetime.now(timezone.utc)
        task_id = str(uuid4())

        # Publish task started event
        await self.event_bus.publish(
            event_type=EventType.AGENT_TASK_STARTED,
            deal_id=deal_id,
            document_id=document_id,
            agent_name=self.name,
            payload={"task_id": task_id, "input_keys": list(input_data.keys())},
        )

        # Initialize state
        initial_state: AgentState = {
            "task_id": task_id,
            "deal_id": str(deal_id) if deal_id else None,
            "document_id": str(document_id) if document_id else None,
            "input_data": input_data,
            "output_data": {},
            "current_step": "",
            "steps_completed": [],
            "errors": [],
            "messages": [],
            "iterations": 0,
            "max_iterations": self.max_iterations,
            "extractions": [],
            "confidence_scores": {},
            "requires_review": False,
        }

        try:
            # Run the graph in a thread pool to avoid blocking the event loop
            final_state = await asyncio.to_thread(
                self._compiled_graph.invoke, initial_state
            )

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            success = len(final_state.get("errors", [])) == 0

            output = AgentOutput(
                agent_name=self.name,
                task_id=task_id,
                success=success,
                output_data=final_state.get("output_data", {}),
                extractions=final_state.get("extractions", []),
                errors=final_state.get("errors", []),
                duration_seconds=duration,
                requires_review=final_state.get("requires_review", False),
            )

            # Publish completion event
            await self.event_bus.publish(
                event_type=EventType.AGENT_TASK_COMPLETED,
                deal_id=deal_id,
                document_id=document_id,
                agent_name=self.name,
                payload={
                    "task_id": task_id,
                    "success": success,
                    "duration_seconds": duration,
                    "requires_review": output.requires_review,
                },
            )

            return output

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"{self.name}: Task {task_id} failed: {e}", exc_info=True)

            # Publish failure event
            await self.event_bus.publish(
                event_type=EventType.AGENT_TASK_FAILED,
                deal_id=deal_id,
                document_id=document_id,
                agent_name=self.name,
                payload={
                    "task_id": task_id,
                    "error": str(e),
                    "duration_seconds": duration,
                },
            )

            return AgentOutput(
                agent_name=self.name,
                task_id=task_id,
                success=False,
                output_data={},
                errors=[str(e)],
                duration_seconds=duration,
            )

    def call_llm(
        self,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """
        Call the LLM API (supports Claude, Groq/Llama, Ollama).

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens in response
            tools: Optional tool definitions (Claude only)

        Returns:
            API response dict with 'content' and 'usage'
        """
        if not self.has_llm:
            raise ValueError("No LLM client available")

        if self._llm_provider == "anthropic":
            return self._call_anthropic(messages, system, max_tokens, tools)
        elif self._llm_provider == "groq":
            return self._call_groq(messages, system, max_tokens)
        elif self._llm_provider == "ollama":
            return self._call_ollama(messages, system)
        else:
            raise ValueError(f"Unknown LLM provider: {self._llm_provider}")

    def _call_anthropic(
        self,
        messages: list[dict[str, str]],
        system: Optional[str],
        max_tokens: int,
        tools: Optional[list[dict]],
    ) -> dict[str, Any]:
        """Call Anthropic/Claude API."""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = tools

        response = self._client.messages.create(**kwargs)

        return {
            "content": response.content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }

    def _call_groq(
        self,
        messages: list[dict[str, str]],
        system: Optional[str],
        max_tokens: int,
    ) -> dict[str, Any]:
        """Call Groq API (Llama 3, Mixtral, etc.)."""
        # Groq uses OpenAI-compatible format
        formatted_messages = []

        if system:
            formatted_messages.append({"role": "system", "content": system})

        formatted_messages.extend(messages)

        response = self._client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            max_tokens=max_tokens,
        )

        # Extract text content
        content_text = response.choices[0].message.content

        return {
            "content": [{"type": "text", "text": content_text}],
            "stop_reason": response.choices[0].finish_reason,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
        }

    def _call_ollama(
        self,
        messages: list[dict[str, str]],
        system: Optional[str],
    ) -> dict[str, Any]:
        """Call Ollama API (local Llama, Mistral, etc.)."""
        formatted_messages = []

        if system:
            formatted_messages.append({"role": "system", "content": system})

        formatted_messages.extend(messages)

        response = self._client.chat(
            model=self.model,
            messages=formatted_messages,
        )

        content_text = response["message"]["content"]

        return {
            "content": [{"type": "text", "text": content_text}],
            "stop_reason": "end",
            "usage": {
                "input_tokens": response.get("prompt_eval_count", 0),
                "output_tokens": response.get("eval_count", 0),
            },
        }

    def get_text_from_response(self, response: dict[str, Any]) -> str:
        """Extract text content from LLM response."""
        content = response.get("content", [])
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    return block.get("text", "")
                if hasattr(block, "text"):
                    return block.text
        return ""

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Override in subclasses to customize.
        """
        return f"""You are {self.name}, a specialized AI agent in the PE-Nexus system.

Your role: {self.description}

Guidelines:
- Always provide accurate, verifiable information
- Include source references for all extracted data
- Express confidence levels for uncertain information
- Flag items that require human review
- Follow the specific task instructions carefully
"""
