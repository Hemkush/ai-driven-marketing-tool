AGENT_REGISTRY = [
    {
        "agent_id": "onboarding_interviewer",
        "purpose": "Generate adaptive follow-up questionnaire questions.",
        "inputs": ["project_id", "session_id", "latest_answers"],
        "outputs": ["next_questions"],
    },
    {
        "agent_id": "segment_analyst",
        "purpose": "Build segment attractiveness analysis from questionnaire data.",
        "inputs": ["project_id", "questionnaire_responses"],
        "outputs": ["analysis_report"],
    },
    {
        "agent_id": "positioning_copilot",
        "purpose": "Draft and refine targeting-positioning statements.",
        "inputs": ["project_id", "analysis_report", "owner_feedback"],
        "outputs": ["positioning_statement"],
    },
    {
        "agent_id": "market_researcher",
        "purpose": "Compile target-customer and competitor research with evidence.",
        "inputs": ["project_id", "analysis_report"],
        "outputs": ["research_report"],
    },
    {
        "agent_id": "persona_builder",
        "purpose": "Generate 2-3 buyer personas with psychographic and behavioral fields.",
        "inputs": ["project_id", "research_report"],
        "outputs": ["persona_profiles"],
    },
    {
        "agent_id": "roadmap_planner",
        "purpose": "Create 90-day implementation plan.",
        "inputs": ["project_id", "personas"],
        "outputs": ["roadmap_plan"],
    },
    {
        "agent_id": "content_studio",
        "purpose": "Generate logos and campaign content assets.",
        "inputs": ["project_id", "roadmap_plan", "content_request"],
        "outputs": ["media_assets"],
    },
]

MCP_REGISTRY = [
    {
        "server_id": "postgres",
        "required": True,
        "role": "Primary structured storage for questionnaire and strategy artifacts.",
    },
    {
        "server_id": "object_storage",
        "required": True,
        "role": "Store generated media assets and logos.",
    },
    {
        "server_id": "web_search",
        "required": True,
        "role": "Ground competitor and customer research with cited sources.",
    },
    {
        "server_id": "maps_places",
        "required": False,
        "role": "Estimate local competitor density and structural competition.",
    },
    {
        "server_id": "trends",
        "required": False,
        "role": "Measure segment growth trends over time.",
    },
]
