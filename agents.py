"""
Multi-agent system — 4 specialized agents for the research pipeline.
"""

import json
from config import CONFIG
from llm_client import llm_call, parse_llm_json
from search import web_search, file_search

PLANNER_PROMPT = """You are a senior research planner. Your job is to decompose a complex research 
question into specific, answerable sub-questions that cover all important angles.

For each sub-question, provide a search query that would find the best information.

Rules:
- 3-5 sub-questions, each targeting a different aspect
- Sub-questions should be specific and searchable, not vague
- Search queries should use keywords likely to surface authoritative sources
- Cover: facts/data, context/background, opposing views, practical implications, future trends

Return valid JSON with this exact structure:
{
  "decomposition_strategy": "brief explanation of your approach",
  "sub_questions": [
    {
      "id": 1,
      "question": "specific sub-question?",
      "search_query": "optimized search keywords",
      "angle": "what aspect this covers"
    }
  ]
}"""


def planner_agent(question: str) -> dict:
    """Plan: decompose the research question into sub-questions."""
    user = f"Research question: {question}\n\nBreak this down into sub-questions."
    response = llm_call(PLANNER_PROMPT, user, temperature=0.2, json_mode=True)
    return parse_llm_json(response, "planner")


# ── Agent 2: SEARCHER ──────────────────────────────────────

SEARCHER_PROMPT = """You are a research analyst specializing in fact extraction. 
Given web search results about a specific sub-question, extract the key facts, 
statistics, quotes, and insights. Be precise and always cite your source URL.

Rules:
- Extract 3-6 key findings, each with a source URL
- Include specific data points, dates, numbers when available
- **Score source freshness**: estimate how recent each source is (current_year=2026, last_year=2025, older=2024-)
- Note any contradictions between sources
- Flag speculation vs. established facts
- If results are low quality, say so honestly

Return valid JSON:
{
  "sub_question": "the question being answered",
  "findings": [
    {
      "fact": "specific finding with context",
      "source_url": "https://...",
      "source_title": "title of source",
      "confidence": "high|medium|low",
      "freshness": "current_year|last_year|older",
      "type": "data_point|quote|analysis|opinion"
    }
  ],
  "quality_assessment": "brief assessment of result quality",
  "missing_information": ["what's still unknown"]
}"""


def searcher_agent(sub_question: dict) -> dict:
    """Search web for a sub-question and extract findings."""
    query = sub_question.get("search_query", sub_question["question"])
    search_results = web_search(query, max_results=CONFIG["search"]["max_results"])

    # Also search local files
    try:
        local_results = file_search(query, max_results=5)
        search_results.extend(local_results)
    except Exception:
        pass  # local search is best-effort

    if not search_results:
        return {
            "sub_question": sub_question["question"],
            "findings": [],
            "quality_assessment": "No search results found",
            "missing_information": ["All sources unavailable"],
        }

    # Format search results for the LLM
    results_text = "\n\n---\n".join(
        f"SOURCE {i+1}: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(search_results)
    )

    user = f"""Sub-question: {sub_question['question']}
Angle: {sub_question.get('angle', 'general')}

Web search results:
{results_text}

Extract key findings from these results."""

    response = llm_call(SEARCHER_PROMPT, user, temperature=0.2, json_mode=True)
    return parse_llm_json(response, "searcher")


# ── Agent 3: ANALYST ───────────────────────────────────────

ANALYST_PROMPT = """You are a research quality analyst. Review all findings collected so far 
against the original research question and identify gaps, contradictions, and weak areas.

Rules:
- Check if the original question is fully answered
- Identify any important angles not covered
- Flag findings with low confidence or dubious sources
- Suggest follow-up searches for gaps
- Be honest: if the research is sufficient, say so

Return valid JSON:
{
  "coverage_score": 1-10,
  "answered_aspects": ["aspects covered"],
  "gaps": [
    {
      "gap": "what's missing",
      "importance": "critical|important|nice_to_have",
      "follow_up_query": "suggested search to fill this gap"
    }
  ],
  "contradictions": [
    {"finding_a": "...", "finding_b": "...", "resolution_note": "..."}
  ],
  "overall_assessment": "brief summary of research quality",
  "needs_more_research": true/false
}"""


def analyst_agent(question: str, all_findings: list[dict]) -> dict:
    """Analyze findings and identify gaps."""
    findings_text = json.dumps(all_findings, indent=2)

    user = f"""Original question: {question}

All findings collected so far:
{findings_text}

Review these findings and identify gaps."""

    response = llm_call(ANALYST_PROMPT, user, temperature=0.3, json_mode=True)
    return parse_llm_json(response, "analyst")


# ── Agent 4: SYNTHESIZER ───────────────────────────────────

SYNTHESIZER_PROMPT = """You are a senior research writer. Synthesize all findings into a 
comprehensive, well-structured report. This is the final deliverable.

Rules:
- Start with an executive summary (2-3 sentences)
- Organize into logical sections with headings
- Include specific data points with citations [Source: title]
- Use tables for comparative data
- Note areas of uncertainty
- End with key takeaways
- Be balanced and objective

Return valid JSON:
{
  "title": "report title",
  "executive_summary": "2-3 sentence overview",
  "sections": [
    {
      "heading": "Section Heading",
      "content": "paragraph text with [Source: name] citations",
      "subsections": [],
      "table": {
        "headers": ["col1", "col2"],
        "rows": [["val1", "val2"]]
      },
      "chart": {
        "type": "bar|line|pie|doughnut|radar",
        "title": "Chart Title",
        "labels": ["Label 1", "Label 2"],
        "datasets": [{
          "label": "Dataset Name",
          "data": [10, 20],
          "backgroundColor": ["#58a6ff", "#3fb950"]
        }]
      }
    }
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2"],
  "uncertainty_notes": ["areas of remaining uncertainty"],
  "sources": [
    {"title": "...", "url": "..."}
  ],
  "research_metadata": {
    "sub_questions_asked": 0,
    "total_findings": 0,
    "iterations": 0,
    "search_queries": []
  }
}"""


def synthesizer_agent(question: str, all_findings: list[dict], metadata: dict) -> dict:
    """Synthesize all findings into a final structured report."""
    findings_text = json.dumps(all_findings, indent=2)
    meta_text = json.dumps(metadata, indent=2)

    user = f"""Original research question: {question}

All findings from research:
{findings_text}

Research metadata:
{meta_text}

Synthesize everything into a comprehensive final report."""

    response = llm_call(SYNTHESIZER_PROMPT, user, temperature=0.4, json_mode=True)
    return parse_llm_json(response, "synthesizer")


