#!/usr/bin/env python3
"""
Demo script — runs the full DeepResearch pipeline on "Which actor is the greatest Batman?"
using simulated agent responses. No API key needed for the demo.
"""

import json, os, sys, threading, uuid, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from server import (
    ResearchSession, SESSIONS, run_research, app, CONFIG,
    save_wiki_note, ensure_vault_structure, update_index, append_log,
)

# ═══════════════════════════════════════════════════════════
# Simulated research data — realistic, cited, multi-iteration
# ═══════════════════════════════════════════════════════════

SIMULATED_REPORT = {
    "title": "Who Is the Greatest Batman Actor? A Multi-Dimensional Analysis",
    "executive_summary": "After analyzing critical reception, box office performance, cultural impact, and acting craft across 8 Batman actors from 1943–2026, Christian Bale leads in critical consensus and box office, while Kevin Conroy dominates as the definitive voice. However, 'greatest' depends on criteria: Bale for realism, Keaton for trailblazing, Conroy for fidelity to source material, and Pattinson for the most psychologically complex portrayal. No single actor wins across all dimensions.",
    "sections": [
        {
            "heading": "The Contenders: All 8 Live-Action Batman Actors Ranked",
            "content": "The Batman mantle has been worn by 8 actors in major live-action theatrical releases: Lewis Wilson (1943), Robert Lowery (1949), Adam West (1966), Michael Keaton (1989–2023), Val Kilmer (1995), George Clooney (1997), Christian Bale (2005–2012), Ben Affleck (2016–2023), and Robert Pattinson (2022–). Kevin Conroy voiced Batman across 30+ years of animation and games, widely considered the definitive portrayal by fans. [Source: Wikipedia Batman Actors]",
            "table": {
                "headers": ["Actor", "Era", "Films", "Rotten Tomatoes Avg", "Box Office (B)"],
                "rows": [
                    ["Christian Bale", "2005–2012", "3 (Nolan Trilogy)", "92%", "$2.46B"],
                    ["Michael Keaton", "1989–2023", "3", "78%", "$1.19B"],
                    ["Robert Pattinson", "2022–", "1", "85%", "$0.77B"],
                    ["Ben Affleck", "2016–2023", "3", "55%", "$2.19B"],
                    ["Adam West", "1966", "1", "81%", "$0.003B"],
                    ["Val Kilmer", "1995", "1", "39%", "$0.34B"],
                    ["George Clooney", "1997", "1", "12%", "$0.24B"],
                    ["Kevin Conroy", "1992–2022", "Voice: 15+", "95% (fans)", "N/A"],
                ]
            }
        },
        {
            "heading": "Critical Consensus: Bale's Trilogy Sets the Gold Standard",
            "content": "Christian Bale's portrayal across Christopher Nolan's Dark Knight Trilogy achieved the highest critical acclaim. The Dark Knight (2008) holds 94% on Rotten Tomatoes with a Metacritic score of 84 — the highest for any superhero film of its era. Roger Ebert called Bale's performance 'the most fully realized Batman on screen.' The trilogy is credited with elevating superhero films to serious cinema, influencing everything from the MCU's darker turns to Joker (2019). However, critics note Bale's Batman voice was divisive. [Source: Rotten Tomatoes, Metacritic, RogerEbert.com]",
            "subsections": [
                {
                    "heading": "The Voice Controversy",
                    "content": "Bale's guttural Batman voice, while iconic, became a subject of parody. Fellow actor Josh Brolin noted that Ben Affleck's electronically modulated voice was 'more intimidating.' This remains the most common criticism of Bale's otherwise celebrated performance."
                }
            ]
        },
        {
            "heading": "Cultural Impact: Keaton vs. West vs. Conroy",
            "content": "Michael Keaton's casting in 1989 was met with fan protests — 50,000 letters to Warner Bros. demanding his removal. His performance silenced critics and redefined Batman for a generation, setting the template for every dark interpretation that followed. Adam West's 1966 campy portrayal created the 'POW! BAM!' cultural lexicon that persists today. Kevin Conroy voiced Batman across Batman: The Animated Series (1992), the Arkham games, and 15+ animated films — for many fans born after 1985, Conroy IS Batman. His death in 2022 prompted an outpouring marking him as the definitive voice of the character. [Source: The Hollywood Reporter, IGN, DC Comics]"
        },
        {
            "heading": "Psychological Depth: Pattinson's Reinvention",
            "content": "Robert Pattinson's The Batman (2022) presented the most psychologically complex live-action Batman — a reclusive, traumatized detective in his second year of crime-fighting. Director Matt Reeves described it as 'Batman as a psychological horror.' The film explores Bruce Wayne's mental health, grief, and the thin line between vigilante justice and vengeance. Critics praised Pattinson for conveying volumes with minimal dialogue. Paul Dano (Riddler) noted Pattinson brought 'real danger' to the role. This interpretation most closely matches the detective-noir roots of the comics. [Source: Variety, Empire, The Ringer]"
        },
        {
            "heading": "Fan Polls and Audience Scores",
            "content": "Across multiple large-scale fan polls, Christian Bale and Kevin Conroy consistently rank 1–2. A 2023 IGN poll of 500,000+ voters placed: 1) Bale (34%), 2) Conroy (28%), 3) Keaton (19%), 4) Pattinson (12%), 5) Affleck (5%), 6) West (2%). On IMDb, The Dark Knight remains the highest-rated Batman film (9.0/10) with over 3 million votes — the only superhero film in the IMDb Top 250's top 5. Conroy's Batman: The Animated Series holds 9.1/10. [Source: IGN, IMDb, Ranker, ComicBook.com]"
        },
        {
            "heading": "The Legacy Argument: Who Changed Batman Forever?",
            "content": "If 'greatest' means most influential, three actors stand out: Adam West made Batman a household name; Michael Keaton proved a dark Batman could succeed commercially; Christian Bale proved superhero films could be prestige cinema. If 'greatest' means most faithful to source material, Kevin Conroy's 30-year run as the voice of Batman across animation, games, and film is unmatched. If 'greatest' means most nuanced performance, Robert Pattinson's noir-detective take breaks new ground. There is no single answer — the question reveals more about what we value in the character than about the actors themselves. [Source: Vulture, The Atlantic, Den of Geek]"
        }
    ],
    "key_takeaways": [
        "Christian Bale leads in combined critical acclaim (92% avg RT) and box office ($2.46B), and The Dark Knight remains the highest-rated superhero film on IMDb at 9.0/10",
        "Kevin Conroy is the definitive Batman for animation/gaming fans — 30 years, 15+ projects, near-universal acclaim from the fanbase",
        "Michael Keaton's 1989 portrayal overcame massive fan backlash to redefine Batman and prove dark superhero films could succeed commercially",
        "Robert Pattinson delivers the most psychologically complex live-action Batman, channeling the detective-noir roots of the comics",
        "George Clooney and Val Kilmer are near-universally considered the weakest portrayals by both critics and fans",
        "The 'greatest' question has no objective answer — it depends entirely on criteria: realism, fidelity, innovation, or psychological depth"
    ],
    "uncertainty_notes": [
        "Fan polls may skew toward younger demographics who grew up with Bale/Conroy",
        "Box office figures are not inflation-adjusted; West's 1966 gross would be ~$350M in 2024 dollars",
        "Robert Pattinson's legacy is incomplete with only one film released (The Batman Part II expected 2027)",
        "Animated/voice performances are evaluated differently than live-action, making direct comparison imperfect"
    ],
    "sources": [
        {"title": "Wikipedia: Batman in film", "url": "https://en.wikipedia.org/wiki/Batman_in_film"},
        {"title": "Rotten Tomatoes: Batman Franchise", "url": "https://www.rottentomatoes.com/franchise/batman"},
        {"title": "IMDb: The Dark Knight (2008)", "url": "https://www.imdb.com/title/tt0468569/"},
        {"title": "IGN: Best Batman Actor Poll (2023)", "url": "https://www.ign.com/articles/best-batman-actor-poll"},
        {"title": "The Hollywood Reporter: Kevin Conroy Obituary", "url": "https://www.hollywoodreporter.com/tv/tv-news/kevin-conroy-dead-batman-voice-actor-1235259944/"},
        {"title": "Variety: The Batman Review", "url": "https://variety.com/2022/film/reviews/the-batman-review-robert-pattinson-1235193075/"},
        {"title": "Roger Ebert: The Dark Knight Review", "url": "https://www.rogerebert.com/reviews/the-dark-knight-2008"},
        {"title": "Vulture: Every Batman Actor Ranked", "url": "https://www.vulture.com/article/batman-actors-ranked.html"},
        {"title": "The Ringer: The Psychology of The Batman", "url": "https://www.theringer.com/movies/2022/3/4/22960309/the-batman-matt-reeves-robert-pattinson"},
        {"title": "Metacritic: The Dark Knight", "url": "https://www.metacritic.com/movie/the-dark-knight/"}
    ],
    "research_metadata": {
        "sub_questions_asked": 5,
        "total_findings": 28,
        "iterations": 3,
        "search_queries": [
            "best Batman actor ranked critics review",
            "Christian Bale Batman performance analysis",
            "Michael Keaton Batman legacy impact",
            "Kevin Conroy Batman voice actor legacy",
            "Robert Pattinson Batman psychological analysis"
        ]
    }
}


def inject_demo_session():
    """Create a pre-loaded demo session with the Batman research."""
    session_id = "demo-batman-01"
    session = ResearchSession(session_id, "Which actor is the greatest Batman and why?")
    session.status = "complete"
    session.report = SIMULATED_REPORT
    session.metadata = SIMULATED_REPORT["research_metadata"]

    # Add simulated progress timeline
    session.progress = [
        {"type": "phase", "data": {"phase": "planning", "message": "Decomposing research question..."}, "time": 0},
        {"type": "plan_complete", "data": {"strategy": "Multi-dimensional analysis across critics, fans, box office, and legacy", "sub_questions": [
            "Who are all the actors who have played Batman in major productions?",
            "How do critics rate each Batman actor's performance?",
            "What is the cultural impact and legacy of each portrayal?",
            "How do fans rank Batman actors in polls?",
            "Which performances broke new ground or redefined the character?"
        ], "count": 5}, "time": 1},
        {"type": "phase", "data": {"phase": "searching", "iteration": 1, "total_iterations": 3, "message": "Research iteration 1/3 — searching 5 angles..."}, "time": 2},
        {"type": "finding_complete", "data": {"sub_question": "Who are all the actors who have played Batman?", "facts_found": 6, "quality": "Comprehensive list compiled from Wikipedia and DC database"}, "time": 3},
        {"type": "finding_complete", "data": {"sub_question": "How do critics rate each Batman actor's performance?", "facts_found": 7, "quality": "Strong — Rotten Tomatoes, Metacritic, and major reviews analyzed"}, "time": 4},
        {"type": "finding_complete", "data": {"sub_question": "What is the cultural impact of each portrayal?", "facts_found": 5, "quality": "Good coverage with historical context"}, "time": 5},
        {"type": "phase", "data": {"phase": "analyzing", "iteration": 1, "message": "Analyzing findings for gaps and contradictions..."}, "time": 6},
        {"type": "analysis_complete", "data": {"coverage_score": 7, "needs_more": True, "gaps": ["Psychological depth analysis missing for Pattinson", "Fan poll data needed for quantitative comparison"], "assessment": "Good foundation. Need fan sentiment data and deeper character analysis."}, "time": 7},
        {"type": "phase", "data": {"phase": "searching", "iteration": 2, "total_iterations": 3, "message": "Research iteration 2/3 — searching 2 gap angles..."}, "time": 8},
        {"type": "finding_complete", "data": {"sub_question": "Fan polls: who is the best Batman?", "facts_found": 6, "quality": "Strong — IGN poll (500K+ voters), IMDb, Ranker data"}, "time": 9},
        {"type": "finding_complete", "data": {"sub_question": "Psychological depth: Pattinson's Batman analyzed", "facts_found": 4, "quality": "Good — Variety, Empire, The Ringer reviews"}, "time": 10},
        {"type": "phase", "data": {"phase": "analyzing", "iteration": 2, "message": "Analyzing expanded findings..."}, "time": 11},
        {"type": "analysis_complete", "data": {"coverage_score": 9, "needs_more": False, "gaps": [], "assessment": "Comprehensive. All major angles covered. Ready for synthesis."}, "time": 12},
        {"type": "phase", "data": {"phase": "synthesizing", "message": "Synthesizing all 28 findings into final report..."}, "time": 13},
        {"type": "report_complete", "data": SIMULATED_REPORT, "time": 14},
        {"type": "phase", "data": {"phase": "complete", "message": "Research complete!"}, "time": 15},
    ]

    SESSIONS[session_id] = session
    return session_id


if __name__ == "__main__":
    session_id = inject_demo_session()
    print("=" * 60)
    print("  🦇 DeepResearch Demo — Batman Test")
    print("=" * 60)
    print(f"  Demo session: {session_id}")
    print(f"  Question: Which actor is the greatest Batman?")
    print(f"  Report sections: {len(SIMULATED_REPORT['sections'])}")
    print(f"  Sources cited: {len(SIMULATED_REPORT['sources'])}")
    print(f"  Findings: {SIMULATED_REPORT['research_metadata']['total_findings']}")
    print("=" * 60)
    print(f"  Server: http://localhost:5000")
    print(f"  Open in browser → paste session ID: {session_id}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=False)
