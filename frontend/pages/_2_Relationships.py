"""
Relationships Page - Relationship Navigator Agent
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client

st.set_page_config(
    page_title="Relationships | PE-Nexus",
    page_icon="link",
    layout="wide",
)

# Header
st.title("Relationship Navigator")
st.markdown("**Find Warm Introduction Paths**")

# Explanation box
st.info("""
**What this agent does:**

The Relationship Navigator maps professional networks to find the best path to reach a target person.
It searches through:
- Firm contacts and their connections
- Board memberships and advisory relationships
- Previous business dealings
- Personal and professional networks

The agent calculates **Path Strength** based on relationship quality and generates **Introduction Drafts**.
""")

# Get API client early for LLM status
api = get_api_client()
llm_status = api.get_llm_status()

# Tech Stack - show current LLM
with st.expander("Tech Stack & AI Model"):
    st.markdown(f"""
    ### Technology Used

    | Component | Technology | Purpose |
    |-----------|------------|---------|
    | **AI Model** | **{llm_status['display_name']}** | Introduction draft generation, context analysis |
    | AI Type | Large Language Model (LLM) | Generative AI with reasoning capabilities |
    | Agent Framework | LangGraph | State machine-based agent orchestration |
    | Graph Algorithm | BFS (Breadth-First Search) | Shortest path finding |
    | Database | PostgreSQL with Recursive CTEs | Relationship graph storage & traversal |
    | Backend | FastAPI + Python | Async API endpoints |

    **Supported LLM Providers:**
    - **Groq** (Llama 3.3 70B) - FREE, 30 req/min
    - **Ollama** (Llama 3.2) - FREE, runs locally
    - **Anthropic** (Claude) - Paid, highest quality

    **How the LLM is used in this agent:**
    - Generates personalized introduction email drafts
    - Creates contextual talking points for introducers
    - Analyzes relationship context and suggests approach strategies
    - Provides natural language summaries of connection paths

    ---

    ### Works Without API Key?  YES

    | Feature | Without API Key | With API Key |
    |---------|-----------------|--------------|
    | Path Finding | BFS algorithm | Same |
    | Path Strength | Calculated from relationship weights | Same |
    | Contact Data | Mock network (17 people, 22 relationships) | Same |
    | Introduction Draft | Template-based | AI-personalized email |
    | Talking Points | Generic list | AI-generated context-aware points |

    *Path finding and network mapping work fully without AI - only email drafts are enhanced.*
    """)

st.markdown("---")

# Check backend status (api already initialized above)
health = api.health_check()
if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server.")
    st.stop()

# Get available contacts
contacts_result = api.navigator_contacts()
contacts = contacts_result.get("contacts", [])

# Build contact list for dropdowns
firm_contacts = [c for c in contacts if c.get("is_firm_contact")]
external_contacts = [c for c in contacts if not c.get("is_firm_contact")]

all_contact_names = [c.get("name", "") for c in contacts]

# Path Finding Section
st.subheader("Find Connection Path")

col1, col2 = st.columns(2)

with col1:
    # From person (typically firm contact)
    from_options = [""] + [c.get("name", "") for c in firm_contacts]
    from_person = st.selectbox(
        "From (Your Contact)",
        options=from_options,
        index=1 if len(from_options) > 1 else 0,
        help="Select a firm contact as the starting point",
    )

    if from_person:
        from_contact = next((c for c in firm_contacts if c.get("name") == from_person), {})
        st.caption(f"Title: {from_contact.get('title', 'N/A')}")
        st.caption(f"Company: {from_contact.get('company', 'N/A')}")

with col2:
    # To person (target)
    to_options = [""] + [c.get("name", "") for c in external_contacts]
    to_person = st.selectbox(
        "To (Target Person)",
        options=to_options,
        index=1 if len(to_options) > 1 else 0,
        help="Select the person you want to reach",
    )

    if to_person:
        to_contact = next((c for c in external_contacts if c.get("name") == to_person), {})
        st.caption(f"Title: {to_contact.get('title', 'N/A')}")
        st.caption(f"Company: {to_contact.get('company', 'N/A')}")

max_hops = st.slider(
    "Maximum Hops",
    min_value=1,
    max_value=4,
    value=3,
    help="Maximum number of intermediaries in the path",
)

# Find Path Button
if st.button("Find Path", type="primary", disabled=not (from_person and to_person)):
    with st.spinner(f"Finding path from {from_person} to {to_person}..."):
        result = api.navigator_find_path(
            from_person=from_person,
            to_person=to_person,
            max_hops=max_hops,
        )

    if result.get("success"):
        output = result.get("output", {})
        paths = output.get("paths", [])
        best_path = output.get("best_path", {})

        if paths:
            st.success(f"Found {len(paths)} path(s)!")

            st.markdown("---")
            st.subheader("Best Path")

            path_col1, path_col2 = st.columns([2, 1])

            with path_col1:
                # Display path visually
                chain = best_path.get("introduction_chain", [])
                if chain:
                    st.markdown("**Connection Chain:**")
                    for i, step in enumerate(chain):
                        if i > 0:
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;|")
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;v")
                        st.markdown(f"**{i+1}.** {step}")

            with path_col2:
                st.metric(
                    label="Path Strength",
                    value=f"{best_path.get('path_strength', 0):.2f}",
                    help="Higher is better (0-1 scale)",
                )
                st.metric(
                    label="Total Hops",
                    value=best_path.get("total_hops", 0),
                )

            # Alternative paths
            if len(paths) > 1:
                st.markdown("---")
                st.subheader("Alternative Paths")

                for i, path in enumerate(paths[1:4], start=2):  # Show up to 3 alternatives
                    with st.expander(f"Path {i} (Strength: {path.get('path_strength', 0):.2f})"):
                        alt_chain = path.get("introduction_chain", [])
                        for step in alt_chain:
                            st.write(f"- {step}")
        else:
            st.warning("No path found within the specified hops. Try increasing max hops.")
    else:
        st.error(f"Path finding failed: {result.get('error', 'Unknown error')}")

# Introduction Draft Section
st.markdown("---")
st.subheader("Generate Introduction Request")

st.markdown("Get a path with a drafted introduction email:")

intro_col1, intro_col2 = st.columns(2)

with intro_col1:
    intro_from = st.selectbox(
        "From (Firm Contact)",
        options=from_options,
        index=1 if len(from_options) > 1 else 0,
        key="intro_from",
    )

with intro_col2:
    intro_to = st.selectbox(
        "To (Target)",
        options=to_options,
        index=1 if len(to_options) > 1 else 0,
        key="intro_to",
    )

context = st.text_area(
    "Context/Purpose",
    value="Exploring potential strategic partnership or investment opportunity",
    help="Provide context for the introduction request",
)

if st.button("Generate Introduction", type="secondary", disabled=not (intro_from and intro_to)):
    with st.spinner("Generating introduction..."):
        result = api.navigator_suggest_intro(
            from_person=intro_from,
            to_person=intro_to,
            context=context,
        )

    if result.get("success"):
        output = result.get("output", {})
        intro_draft = output.get("introduction_draft", {})
        best_path = output.get("best_path", {})

        st.success("Introduction generated!")

        st.markdown("---")

        # Show the path
        st.subheader("Recommended Path")
        chain = best_path.get("introduction_chain", [])
        if chain:
            st.write(" -> ".join(chain))

        # Show introducer info
        introducer = intro_draft.get("introducer", {})
        if introducer:
            st.markdown(f"**Key Introducer:** {introducer.get('name', 'Unknown')}")
            st.markdown(f"*{introducer.get('title', '')} at {introducer.get('company', '')}*")

        # Show draft email
        st.markdown("---")
        st.subheader("Draft Introduction Request")

        subject = intro_draft.get("subject", "Introduction Request")
        body = intro_draft.get("body", "")

        st.text_input("Subject", value=subject, disabled=True)

        if body:
            st.text_area("Email Body", value=body, height=250)

            # Copy button
            st.download_button(
                label="Download Draft",
                data=f"Subject: {subject}n\n{body}",
                file_name="intro_request.txt",
                mime="text/plain",
            )

        # Talking points
        talking_points = intro_draft.get("talking_points", [])
        if talking_points:
            st.markdown("---")
            st.subheader("Talking Points for Introducer")
            for point in talking_points:
                st.write(f"- {point}")
    else:
        st.error(f"Introduction generation failed: {result.get('error', 'Unknown error')}")

# Network Map Section
st.markdown("---")
st.subheader("Network Map")

st.markdown("Explore the network around a person:")

map_col1, map_col2 = st.columns(2)

with map_col1:
    map_person = st.selectbox(
        "Center Person",
        options=[""] + all_contact_names,
        index=1 if all_contact_names else 0,
        key="map_person",
    )

with map_col2:
    map_depth = st.slider(
        "Network Depth",
        min_value=1,
        max_value=3,
        value=2,
        key="map_depth",
    )

if st.button("Map Network", disabled=not map_person):
    with st.spinner(f"Mapping network around {map_person}..."):
        result = api.navigator_map_network(
            person=map_person,
            depth=map_depth,
        )

    if result.get("success"):
        output = result.get("output", {})
        network = output.get("network", {})

        center = network.get("center", {})  # API returns "center" not "center_person"
        nodes = network.get("nodes", [])
        edges = network.get("edges", [])

        # Build connections with degree info
        # First, build a lookup of edges by person
        center_id = center.get("id", "")

        # BFS to assign degrees
        node_degrees = {center_id: 0}
        edge_lookup = {}  # node_id -> list of (neighbor_id, relationship_type)

        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            rel_type = edge.get("type", "connected")

            if src not in edge_lookup:
                edge_lookup[src] = []
            if tgt not in edge_lookup:
                edge_lookup[tgt] = []

            edge_lookup[src].append((tgt, rel_type))
            edge_lookup[tgt].append((src, rel_type))

        # Assign degrees using BFS
        queue = [center_id]
        visited = {center_id}
        while queue:
            current = queue.pop(0)
            current_degree = node_degrees.get(current, 0)
            for neighbor, _ in edge_lookup.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    node_degrees[neighbor] = current_degree + 1
                    queue.append(neighbor)

        # Build node lookup
        node_lookup = {n.get("id"): n for n in nodes}

        # Build connections list (excluding center)
        connections = []
        for node in nodes:
            node_id = node.get("id", "")
            if node_id == center_id:
                continue

            degree = node_degrees.get(node_id, 1)

            # Find relationship type from edge
            rel_type = "connected"
            for neighbor, r_type in edge_lookup.get(node_id, []):
                if node_degrees.get(neighbor, 999) < degree:
                    rel_type = r_type.replace("_", " ")
                    break

            connections.append({
                "degree": degree,
                "person": node,
                "relationship": rel_type,
            })

        st.success(f"Found {len(connections)} connections")

        # Display center person
        st.markdown(f"**{center.get('name', map_person)}**")
        st.caption(f"{center.get('title', '')} at {center.get('company', '')}")

        # Display connections by degree
        if connections:
            st.markdown("---")

            # Group by degree
            by_degree = {}
            for conn in connections:
                degree = conn.get("degree", 1)
                if degree not in by_degree:
                    by_degree[degree] = []
                by_degree[degree].append(conn)

            for degree in sorted(by_degree.keys()):
                st.markdown(f"**{degree}-degree connections:**")
                for conn in by_degree[degree]:
                    person = conn.get("person", {})
                    rel = conn.get("relationship", "connected")
                    st.write(f"- {person.get('name', 'Unknown')} ({person.get('company', '')}) - {rel}")
        else:
            st.info("No connections found for this person at this depth.")
    else:
        st.error(f"Network mapping failed: {result.get('error', 'Unknown error')}")

# Contact Directory
st.markdown("---")
st.subheader("Contact Directory")

filter_type = st.radio(
    "Filter",
    options=["All", "Firm Contacts", "External"],
    horizontal=True,
)

filter_map = {"All": "all", "Firm Contacts": "firm", "External": "external"}

if contacts:
    import pandas as pd

    filtered = contacts
    if filter_type == "Firm Contacts":
        filtered = firm_contacts
    elif filter_type == "External":
        filtered = external_contacts

    df_data = []
    for c in filtered:
        df_data.append({
            "Name": c.get("name", ""),
            "Title": c.get("title", ""),
            "Company": c.get("company", ""),
            "Type": "Firm" if c.get("is_firm_contact") else "External",
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No contacts available. Run seed_network.py to populate data.")
