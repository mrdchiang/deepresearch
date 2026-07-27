"""
Research templates — pre-built prompts for common research types.
Used by the planner agent to guide decomposition strategy.
"""

TEMPLATES = {
    "competitive_analysis": {
        "name": "Competitive Analysis",
        "description": "Compare products, companies, or solutions",
        "prompt_prefix": "Conduct a competitive analysis comparing {}. Cover: market position, feature comparison, pricing, strengths/weaknesses, and market share.",
    },
    "due_diligence": {
        "name": "Due Diligence",
        "description": "Investigate a company, person, or opportunity",
        "prompt_prefix": "Perform due diligence on {}. Cover: background, financials, reputation, risks, regulatory issues, and key people.",
    },
    "literature_review": {
        "name": "Literature Review",
        "description": "Survey academic or industry research on a topic",
        "prompt_prefix": "Conduct a literature review on {}. Cover: key theories, major findings, methodological approaches, debates, and gaps in current research.",
    },
    "market_sizing": {
        "name": "Market Sizing",
        "description": "Estimate market size, growth, and trends",
        "prompt_prefix": "Size the market for {}. Cover: TAM/SAM/SOM, growth rate, key drivers, major players, geographic breakdown, and 5-year forecast.",
    },
    "technology_assessment": {
        "name": "Technology Assessment",
        "description": "Evaluate a technology, tool, or framework",
        "prompt_prefix": "Assess the technology {}. Cover: how it works, maturity, adoption, alternatives, pros/cons, cost, and future outlook.",
    },
    "policy_analysis": {
        "name": "Policy Analysis",
        "description": "Analyze regulations, laws, or policy proposals",
        "prompt_prefix": "Analyze the policy/regulation {}. Cover: background, key provisions, stakeholders, impact assessment, comparisons to other jurisdictions, and controversy.",
    },
    "trend_forecast": {
        "name": "Trend Forecast",
        "description": "Forecast future developments in a domain",
        "prompt_prefix": "Forecast trends in {}. Cover: current state, emerging signals, expert predictions, data projections, risks, and 5-10 year outlook.",
    },
    "root_cause_analysis": {
        "name": "Root Cause Analysis",
        "description": "Investigate why something happened",
        "prompt_prefix": "Investigate the root causes of {}. Cover: timeline, contributing factors, systemic issues, stakeholder perspectives, and lessons learned.",
    },
    "build_vs_buy": {
        "name": "Build vs Buy Analysis",
        "description": "Compare building in-house vs purchasing",
        "prompt_prefix": "Analyze build vs buy for {}. Cover: cost comparison, time to market, customization needs, maintenance burden, vendor landscape, and total cost of ownership.",
    },
    "custom": {
        "name": "Custom Research",
        "description": "Free-form research question",
        "prompt_prefix": None,  # use the question as-is
    },
}


def get_template(template_id: str) -> dict:
    """Get a research template by ID. Returns None if not found."""
    return TEMPLATES.get(template_id)


def list_templates() -> list[dict]:
    """List all available templates."""
    return [
        {"id": tid, "name": t["name"], "description": t["description"]}
        for tid, t in TEMPLATES.items()
    ]


def apply_template(template_id: str, subject: str) -> str:
    """Apply a template to a subject, returning the full research prompt."""
    template = get_template(template_id)
    if not template or not template.get("prompt_prefix"):
        return subject
    return template["prompt_prefix"].format(subject)
