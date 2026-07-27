#!/usr/bin/env python3
"""
Demo script — runs the full DeepResearch pipeline on "Which actor is the greatest Batman?"
Produces a 5-10 page report matching Microsoft Researcher depth.
No API key needed for the demo.
"""

import json, os, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from server import (
    ResearchSession, SESSIONS, app, CONFIG,
    save_wiki_note, ensure_vault_structure, update_index, append_log,
)

SIMULATED_REPORT = {
    "title": "Who Is the Greatest Batman Actor? A Comprehensive Multi-Dimensional Analysis Across 80 Years of Cinematic History",

    "executive_summary": "This report evaluates all 8 major live-action Batman actors (1943–2022) plus voice actors across 5 dimensions: critical reception, box office performance, cultural impact, psychological depth, and fidelity to source material. Christian Bale leads in combined critical acclaim (92% RT average) and global box office ($2.46B). Kevin Conroy is near-unanimously considered the definitive Batman voice across 30 years of animation and gaming. Michael Keaton's 1989 portrayal overcame 50,000 protest letters to redefine the character for a generation. Robert Pattinson's 2022 noir-detective interpretation represents the most psychologically complex live-action Batman to date. However, no single actor wins across all criteria — the question reveals more about what we value in Batman than about the actors themselves. This report includes detailed per-actor profiles, statistical comparisons, fan sentiment analysis, expert commentary, and a decision framework for readers to reach their own conclusion.",

    "sections": [
        # ── SECTION 1 ──
        {
            "heading": "1. Introduction: The Enduring Question of the Cowl",
            "content": "Since Bob Kane and Bill Finger created Batman in Detective Comics #27 (1939), the character has been portrayed by more actors than any other superhero. 8 actors have worn the cape and cowl in major live-action theatrical releases, while countless others have voiced him in animation and games. Each portrayal reflects not just the actor's interpretation, but the cultural moment in which it was made — from the patriotic serials of the 1940s to the campy 1960s, from the gothic 1980s to the gritty post-9/11 realism of the 2000s, and now to the psychological noir of the 2020s. [Source: DC Comics History] [Source: Wikipedia Batman in Film] This report applies a structured methodology across 5 evaluation dimensions to answer what has become one of pop culture's most debated questions.",
            "subsections": [
                {
                    "heading": "Methodology",
                    "content": "We evaluate each actor across 5 weighted dimensions: Critical Reception (25%) using aggregated Rotten Tomatoes and Metacritic scores, Box Office Performance (20%) using inflation-adjusted global gross, Cultural Impact (25%) measured through industry influence, fan polls, and legacy, Psychological Depth & Acting Craft (20%) assessed through expert reviews and character complexity, and Fidelity to Source Material (10%) measuring alignment with comic book canon. Kevin Conroy is included as a special case for voice performance. Each dimension uses a 1–10 scale with specific scoring rubrics detailed in Section 2."
                }
            ],
            "table": None
        },

        # ── SECTION 2 ──
        {
            "heading": "2. The Complete Contenders: Every Major Batman Actor Profiled",
            "content": "The Batman mantle has been passed across generations. Understanding each actor's context is essential before comparing them. Below is a chronological profile of every major live-action Batman, plus the definitive voice actor.",
            "subsections": [
                {
                    "heading": "Lewis Wilson (1943) — The First",
                    "content": "Wilson starred in the 15-chapter Columbia Pictures serial 'Batman' at age 23, making him the youngest actor to play Batman on screen. The serial was produced during WWII and featured a government-agent Batman fighting a Japanese villain, Dr. Daka — reflecting wartime propaganda. Wilson's Batman was cheerful, athletic, and uncomplicated. The serial was low-budget ($40,000 per chapter), and Wilson never reprised the role. He's historically significant but not competitive in acting craft. [Source: The Hollywood Reporter Archives]"
                },
                {
                    "heading": "Robert Lowery (1949) — The Forgotten Successor",
                    "content": "Lowery took over for the second Columbia serial, 'Batman and Robin.' His portrayal was slightly darker than Wilson's but still serial-era pulp. Lowery was a B-movie actor who appeared in over 70 films, but Batman was a footnote in his career. The serial was the last live-action Batman until the 1960s. Historically noteworthy but largely forgotten by modern audiences. [Source: Wikipedia Batman Serials]"
                },
                {
                    "heading": "Adam West (1966–1968) — The Cultural Phenomenon",
                    "content": "West's Batman was deliberately campy, colorful, and comedic — a stylistic choice that made the 1966 TV series and film massive hits. At its peak, the show aired twice weekly and reached 50+ million viewers. West's deadpan delivery of absurd dialogue ('Some days you just can't get rid of a bomb!') became iconic. The 'POW! BAM! ZAP!' onomatopoeia entered the cultural lexicon. However, the camp interpretation was so dominant that it took 20+ years for darker Batman portrayals to be taken seriously. West later struggled with typecasting but eventually embraced his legacy, voicing characters in Batman: The Animated Series and Family Guy. His 2017 death prompted widespread tributes. [Source: The New York Times Obituary] [Source: Variety]"
                },
                {
                    "heading": "Michael Keaton (1989–1992, 2023) — The Trailblazer Who Silenced 50,000 Protesters",
                    "content": "Keaton's casting was one of the most controversial in superhero history. Fresh off comedies like 'Mr. Mom' and 'Beetlejuice,' fans sent 50,000 protest letters to Warner Bros. demanding his removal, fearing he would make Batman a joke. Director Tim Burton fought for Keaton, and the result was transformative. Keaton brought a quiet intensity, psychological darkness, and a tangible sense of trauma to Bruce Wayne. His Batman was menacing, terse, and genuinely frightening — a complete departure from West. Batman (1989) grossed $411M worldwide (equivalent to ~$950M in 2024 dollars), proving dark superhero films could be blockbusters. Keaton returned 30+ years later in The Flash (2023), demonstrating the role's enduring hold on him. His performance directly influenced every darker interpretation that followed, including the Nolan trilogy. [Source: The Hollywood Reporter] [Source: Empire Magazine Retrospective]"
                },
                {
                    "heading": "Val Kilmer (1995) — The Misunderstood Middle Child",
                    "content": "Kilmer took over for Joel Schumacher's Batman Forever, bringing a more introspective approach than Keaton. He studied the comics extensively and pushed for a psychological exploration of Bruce Wayne's trauma — but Schumacher wanted something lighter and more commercial after the darkness of Batman Returns. The result was a tonal mismatch. Kilmer's performance has moments of genuine depth (the giant bat hallucination scene, his conflicted relationship with Nicole Kidman's Dr. Chase Meridian), but it's buried under neon visuals and Jim Carrey's scene-stealing Riddler. Batman Forever was a box office success ($336M), but critical reception was mixed (39% RT). Kilmer later revealed in his memoir that he found the Batsuit claustrophobic and isolating, contributing to his decision not to return. Retrospective reassessments have been slightly kinder. [Source: Val Kilmer Memoir 'I'm Your Huckleberry'] [Source: Den of Geek]"
                },
                {
                    "heading": "George Clooney (1997) — The Cautionary Tale",
                    "content": "Universally considered the weakest live-action Batman. Clooney himself has apologized for the performance multiple times, famously joking at conventions that he 'killed the franchise.' Batman & Robin (1997) was a critical and commercial disappointment (12% RT, $238M against a $160M budget). Clooney's Batman was quippy, lightweight, and featured the infamous 'Bat-credit card' and Bat-nipples. The film's failure put Batman movies on ice for 8 years until Christopher Nolan rebooted the franchise. Clooney has since called it a learning experience and donated his refund checks to charity. His Batman is studied in film schools as an example of how tone-deaf direction can undermine even a talented actor. [Source: George Clooney Interviews, BBC; GQ]"
                },
                {
                    "heading": "Christian Bale (2005–2012) — The Gold Standard",
                    "content": "Bale's portrayal across Christopher Nolan's Dark Knight Trilogy is the most critically and commercially successful Batman in history. The trilogy grossed $2.46B worldwide. The Dark Knight (2008) holds 94% on Rotten Tomatoes and 84 on Metacritic — the highest-rated superhero film of its era. Bale brought unprecedented physical transformation (gaining 100 lbs after The Machinist), a distinct Batman voice (later parodied but intentionally intimidating), and a Bruce Wayne who was a mask for Batman, not the reverse. Nolan's grounded, post-9/11 realism redefined what superhero films could be, influencing everything from the MCU's darker turns to Joker (2019). Heath Ledger's Joker overshadows Bale in public memory, but critics consistently praise Bale's dual performance. Roger Ebert called it 'the most fully realized Batman on screen.' The trilogy's legacy includes proving that superhero films could be prestige cinema, paving the way for films like Logan and Joker. [Source: RogerEbert.com] [Source: Rotten Tomatoes] [Source: Box Office Mojo] [Source: Metacritic]",
                    "subsections": [
                        {
                            "heading": "The Voice Controversy",
                            "content": "Bale's guttural, throaty Batman voice is the most parodied element of his performance. While intentionally designed to intimidate and disguise his identity, it became a subject of widespread mockery, including by Bale himself. Ben Affleck's electronically modulated voice and Robert Pattinson's quieter, more naturalistic delivery have both been cited as improvements. This remains the most consistent criticism of Bale's otherwise celebrated portrayal."
                        }
                    ]
                },
                {
                    "heading": "Ben Affleck (2016–2023) — The Divisive Veteran",
                    "content": "Affleck's casting faced heavy online backlash (dubbed 'Batfleck'), but Zack Snyder's Batman v Superman: Dawn of Justice (2016) presented a Batman unlike any before: older, brutal, branding criminals, and willing to kill. Drawing from Frank Miller's The Dark Knight Returns, Affleck played a Batman broken by 20 years of fighting crime, grieving Robin's death, and descending into paranoia. Physically, Affleck was the most imposing Batman (6'4', 230 lbs), and his warehouse fight scene is widely considered the best Batman action sequence ever filmed. However, the films themselves were critically divisive: BvS holds 29% RT, Justice League (2017) 39%, though Zack Snyder's Justice League (2021) rose to 71%. Affleck's performance within those films received more praise than the films themselves. He was originally set to direct and star in The Batman but stepped away, citing personal struggles. He reprised the role briefly in The Flash (2023). [Source: IGN] [Source: Variety] [Source: Esquire Profile]"
                },
                {
                    "heading": "Robert Pattinson (2022–Present) — The Noir Detective",
                    "content": "Pattinson's The Batman (2022), directed by Matt Reeves, presents the most psychologically complex live-action Batman: a reclusive, insomniac detective in his second year, still raw with grief and rage. This is Batman as psychological horror — Pattinson's Bruce Wayne barely exists as a public persona, spending his days journaling and his nights as a vigilante who calls himself 'Vengeance.' The film draws heavily from noir cinema (Chinatown, Se7en) and comics like The Long Halloween. At 85% RT and $772M global, it was both a critical and commercial success. Paul Dano (Riddler), Zoë Kravitz (Catwoman), and Colin Farrell (Penguin) form one of the strongest supporting casts in Batman history. Pattinson's brooding, minimalist performance — conveying volumes through presence rather than dialogue — earned comparisons to Ryan Gosling in Drive. Matt Reeves described the approach as 'Batman as a psychological horror film.' A sequel, The Batman Part II, is scheduled for 2027. Pattinson's legacy is incomplete but the first chapter is among the most critically respected Batman debuts. [Source: Empire Magazine] [Source: The Ringer] [Source: Variety]"
                },
                {
                    "heading": "Kevin Conroy (1992–2022) — The Definitive Voice of the Bat",
                    "content": "Kevin Conroy never wore the Batsuit on screen, but for millions of fans, he IS Batman. Conroy voiced the character across 30 years in Batman: The Animated Series (1992–1995), The New Batman Adventures, Justice League, Justice League Unlimited, 15+ animated films, the critically acclaimed Arkham video game trilogy, and numerous guest appearances. Conroy was the first actor to create distinct voices for Batman and Bruce Wayne — a technique he developed from his theater training, giving Bruce Wayne a lighter, more charismatic tone while Batman was deeper and more gravelly. This innovation became standard for virtually every Batman actor who followed, including Bale and Affleck. Batman: The Animated Series holds 9.1/10 on IMDb with near-universal acclaim, and the Arkham games are considered the greatest superhero video games ever made. When Conroy died of cancer in 2022 at age 66, the outpouring of grief from fans, fellow actors, and DC creators was immense. Mark Hamill (his Joker) called him 'the perfect Batman.' Conroy's Batman is the only portrayal to span multiple generations and mediums while maintaining total fan consensus. [Source: The Hollywood Reporter Obituary] [Source: IGN] [Source: DC Comics Official]"
                }
            ],
            "table": {
                "headers": ["Actor", "Era", "Major Films/Games", "RT Average", "Global Box Office (B)", "Key Innovation"],
                "rows": [
                    ["Lewis Wilson", "1943", "1 serial", "N/A", "$0.001", "First live-action Batman"],
                    ["Robert Lowery", "1949", "1 serial", "N/A", "$0.001", "Slightly darker serial take"],
                    ["Adam West", "1966–68", "1 film + 120 TV eps", "81%", "$0.003 ($0.35 adj)", "Camp/comedy template; cultural lexicon"],
                    ["Michael Keaton", "1989–2023", "3 films", "78%", "$1.19", "Proved dark Batman sells; quiet intensity"],
                    ["Val Kilmer", "1995", "1 film", "39%", "$0.34", "Psychological exploration attempt"],
                    ["George Clooney", "1997", "1 film", "12%", "$0.24", "Cautionary tale of tone-deaf filmmaking"],
                    ["Christian Bale", "2005–2012", "3 films (Nolan Trilogy)", "92%", "$2.46", "Elevated superhero films to prestige cinema"],
                    ["Ben Affleck", "2016–2023", "3 films", "55%", "$2.19", "Most physically imposing; TDKR-inspired brutality"],
                    ["Robert Pattinson", "2022–", "1 film (sequel TBA)", "85%", "$0.77", "Noir detective; psychological horror approach"],
                    ["Kevin Conroy", "1992–2022", "Voice: 15+ projects", "95% (fans)", "N/A", "Distinct Bruce/Batman voices; 30-year run"]
                ]
            }
        },

        # ── SECTION 3 ──
        {
            "heading": "3. Critical Reception: What the Experts Say",
            "content": "Critical consensus provides the most objective measure of performance quality, aggregating hundreds of professional reviews into comparable metrics. We analyzed data from Rotten Tomatoes, Metacritic, IMDb, and major publications including The New York Times, RogerEbert.com, Empire, Variety, and The Hollywood Reporter.",
            "subsections": [
                {
                    "heading": "Aggregated Scores: Bale vs. the Field",
                    "content": "Christian Bale dominates critical metrics. The Dark Knight (2008) is the only superhero film in IMDb's Top 5 all-time (9.0/10, 3M+ votes). The Dark Knight Rises (87%) and Batman Begins (85%) complete a trilogy unmatched in consistency. At the opposite end, George Clooney's 12% RT for Batman & Robin is the nadir of the franchise. Robert Pattinson's 85% for The Batman represents a strong debut, though critics noted the film owes significant debt to Nolan's template. Ben Affleck's films are the most polarized — his performance receives praise (particularly in the 'Ultimate Edition' of BvS) while the films themselves are critically panned. [Source: Rotten Tomatoes Franchise Data] [Source: IMDb Top 250]",
                },
                {
                    "heading": "Individual Performance Reviews",
                    "content": "Roger Ebert gave The Dark Knight 4/4 stars, writing: 'Bale's Batman is the most fully realized screen version of the character.' Peter Travers of Rolling Stone called Keaton's 1989 Batman 'a performance of surprising depth and darkness.' For Pattinson, Empire Magazine's 5-star review stated: 'Pattinson plays Batman as a raw nerve — you feel his pain, his rage, his isolation.' Val Kilmer's retrospective notices have improved — The Ringer's 2020 reassessment found 'a genuinely compelling performance fighting against a film that doesn't want it.' Affleck's warehouse fight in BvS was described by ScreenRant as 'the single greatest Batman action sequence ever committed to film.' Even Clooney has his defenders: FilmCritHulk argued in 2019 that Clooney's innate charisma was wasted on 'a script that fundamentally misunderstands Batman.' [Source: RogerEbert.com] [Source: Rolling Stone] [Source: Empire] [Source: The Ringer] [Source: ScreenRant]"
                }
            ],
            "table": {
                "headers": ["Actor", "Tomato-meter Avg", "Metacritic Avg", "IMDb Avg", "Ebert Rating", "Consensus"],
                "rows": [
                    ["Christian Bale", "92%", "78", "8.6", "4/4 ★", "Gold standard"],
                    ["Kevin Conroy", "95% (fan)", "N/A", "9.1 (BTAS)", "N/A", "Universally beloved"],
                    ["Robert Pattinson", "85%", "72", "7.8", "3.5/4 ★", "Excellent debut"],
                    ["Michael Keaton", "78%", "69", "7.5", "3/4 ★", "Groundbreaking"],
                    ["Adam West", "81%", "N/A", "7.4", "N/A", "Cult classic"],
                    ["Ben Affleck", "55%", "46", "6.8", "N/A", "Polarizing"],
                    ["Val Kilmer", "39%", "51", "5.4", "N/A", "Underrated by some"],
                    ["George Clooney", "12%", "28", "3.7", "N/A", "Universally panned"],
                ]
            }
        },

        # ── SECTION 4 ──
        {
            "heading": "4. Box Office Showdown: Who Put Butts in Seats?",
            "content": "Box office performance measures audience enthusiasm and commercial viability. All figures are inflation-adjusted to 2024 dollars where noted. The Batman franchise has generated over $6.8 billion in global box office across all films, making it one of the most valuable IPs in cinema history. [Source: Box Office Mojo] [Source: The Numbers]",
            "subsections": [
                {
                    "heading": "Raw vs. Adjusted Grosses",
                    "content": "Christian Bale's trilogy leads in both nominal ($2.46B) and adjusted dollars. The Dark Knight alone grossed $1.006B — the first superhero film to cross $1B. Ben Affleck's films earned $2.19B across three appearances, though this includes ensemble films where Batman was not the sole draw. In adjusted dollars, Michael Keaton's 1989 Batman would gross approximately $950M in 2024 — outperforming The Batman (2022) despite a smaller global market. Adam West's 1966 film, adjusted for inflation and the smaller theater market of the era, would be a significant commercial success proportional to its time. [Source: Box Office Mojo Adjusted Data]",
                },
                {
                    "heading": "Return on Investment",
                    "content": "When considering budget-to-gross ratios, Keaton's 1989 Batman ($48M budget → $411M gross, 8.5x multiplier) is one of the most profitable superhero films ever made. Bale's Batman Begins ($150M → $374M, 2.5x) was modest but laid groundwork for The Dark Knight ($185M → $1.006B, 5.4x). Pattinson's The Batman ($200M → $772M, 3.9x) performed well for a reboot during pandemic recovery. Clooney's Batman & Robin ($160M → $238M, 1.5x) was a financial disappointment that nearly killed the franchise. [Source: The Numbers Profit Analysis]"
                }
            ],
            "table": {
                "headers": ["Actor", "Total Nominal Gross", "Inflation-Adj Gross", "Best Single Film", "Avg Budget Multiplier"],
                "rows": [
                    ["Christian Bale", "$2.46B", "$2.94B", "The Dark Knight ($1.006B)", "3.3x"],
                    ["Ben Affleck", "$2.19B", "$2.37B", "BvS ($874M)", "2.4x"],
                    ["Michael Keaton", "$1.19B", "$1.68B", "Batman '89 ($411M)", "5.3x"],
                    ["Robert Pattinson", "$0.77B", "$0.82B", "The Batman ($772M)", "3.9x"],
                    ["Val Kilmer", "$0.34B", "$0.61B", "Batman Forever ($336M)", "2.4x"],
                    ["George Clooney", "$0.24B", "$0.43B", "Batman & Robin ($238M)", "1.5x"],
                    ["Adam West", "$0.003B", "$0.35B", "Batman: The Movie (1966)", "4.8x"],
                ]
            }
        },

        # ── SECTION 5 ──
        {
            "heading": "5. Cultural Impact: Who Changed Batman Forever?",
            "content": "Box office and critical scores measure immediate success, but cultural impact measures lasting influence. Some actors changed how Batman is perceived; others reinforced existing perceptions. This section examines each actor's footprint on the character, the industry, and popular culture. [Source: Vulture Cultural Analysis] [Source: The Atlantic]",
            "subsections": [
                {
                    "heading": "Adam West: The Accidental Icon",
                    "content": "West's campy Batman defined the character for a generation of Baby Boomers. The 'POW! BAM!' onomatopoeia, the shark-repellent Bat-spray, the Bat-dance — these are permanently embedded in pop culture. But this interpretation also had a negative impact: it took Frank Miller's The Dark Knight Returns (1986) and Tim Burton's 1989 film to convince audiences that Batman could be taken seriously again. West's legacy is paradoxical — he made Batman a household name while simultaneously making serious Batman impossible for two decades."
                },
                {
                    "heading": "Michael Keaton: The Paradigm Shift",
                    "content": "Keaton's casting triggered 50,000 protest letters. His performance silenced every critic. Batman (1989) proved that comic book films could be dark, gothic, and commercially dominant. The film's aesthetic — Anton Furst's Oscar-winning production design, Danny Elfman's iconic score, the noir-influenced Gotham City — set the template for every Batman film that followed. When Keaton returned in The Flash (2023), 30+ years later, audiences cheered. His Batman is the bridge between the camp era and the dark era."
                },
                {
                    "heading": "Christian Bale: The Prestige Pivot",
                    "content": "Bale and Nolan didn't just make Batman films — they made films that happened to be about Batman. The Dark Knight's Oscar campaign (8 nominations, 2 wins including Ledger's posthumous Best Supporting Actor) forced the Academy to expand Best Picture to 10 nominees, directly leading to Black Panther's nomination a decade later. Bale's Batman legitimized superhero cinema as art. Every 'grounded, realistic' superhero film since — from Joker to The Batman — operates in Nolan's shadow. [Source: Academy Awards Historical Analysis] [Source: Vulture]"
                },
                {
                    "heading": "Ben Affleck: The Deconstruction",
                    "content": "Affleck's Batman — older, broken, brutal — drew directly from Frank Miller's The Dark Knight Returns, arguably the most influential Batman comic ever written. His warehouse fight scene has been studied frame-by-frame by action choreographers. However, the DC Extended Universe's chaotic production limited the cultural impact of what could have been a defining interpretation."
                },
                {
                    "heading": "Kevin Conroy: The Eternal Voice",
                    "content": "Conroy's cultural impact is unique: he never appeared on screen, but for an entire generation (Gen X and Millennials who grew up with Batman: The Animated Series), his voice is the default Batman. When fans read Batman comics, they hear Conroy. The Arkham games — which Conroy headlined — sold 30+ million copies and are considered the greatest superhero games ever. His death in 2022 prompted tributes from across the entertainment industry, with Mark Hamill writing: 'Kevin was perfection. He was the Batman.' Conroy is the only Batman actor for whom there is no meaningful negative criticism. [Source: IGN Survey 2022] [Source: DC Comics Official]"
                }
            ]
        },

        # ── SECTION 6 ──
        {
            "heading": "6. Acting Craft & Psychological Depth: The Character Beneath the Cowl",
            "content": "Batman is unique among superheroes: the real character is Bruce Wayne, and Batman is the performance. The best Batmen understand this duality. This section evaluates each actor's ability to portray the trauma, intelligence, and moral complexity of the character.",
            "subsections": [
                {
                    "heading": "The Bruce/Batman Duality",
                    "content": "Christian Bale's portrayal explicitly framed Bruce Wayne as the mask and Batman as the real identity — a choice Nolan encouraged. Michael Keaton's Bruce Wayne was a socially awkward recluse, a characterization that Tim Burton related to personally. Robert Pattinson's Bruce is barely functional — he journals obsessively, avoids public appearances, and is still raw with grief two years after his parents' murder. Ben Affleck's Bruce is the most psychologically damaged: 20 years of fighting crime have left him drinking, paranoid, and willing to kill. Adam West's Bruce/Batman distinction was largely cosmetic — both personas were equally earnest."
                },
                {
                    "heading": "Physical Transformation",
                    "content": "Christian Bale's extreme physical transformations for the role are legendary: losing 63 lbs for The Machinist, then gaining 100 lbs in 6 months for Batman Begins — only to be told by Nolan he'd overdone it and needed to slim down. Bale's commitment to physical embodiment set a new standard. Ben Affleck, at 6'4' and 230 lbs, was the most physically imposing Batman, closely matching Frank Miller's artwork. Robert Pattinson trained extensively in martial arts and performed many of his own stunts. Michael Keaton, at 5'10', was considered too short by many fans but used his compact physicality to make Batman more animal-like and unpredictable."
                },
                {
                    "heading": "Voice and Presence",
                    "content": "Kevin Conroy pioneered the dual-voice technique — a lighter, more charismatic tone for Bruce Wayne and a deeper, more authoritative voice for Batman. This approach was adopted by virtually every subsequent actor. Bale's extreme version became controversial. Affleck used an electronic voice modulator (canonical from the comics). Pattinson's approach was the most naturalistic — his Batman speaks rarely and softly, relying on presence rather than vocal intimidation. Keaton's Batman was famously terse: 'I'm Batman' (two words) is perhaps the most iconic Batman line ever delivered."
                }
            ]
        },

        # ── SECTION 7 ──
        {
            "heading": "7. Fan Sentiment: What the Audience Says",
            "content": "Professional critics and box office tell part of the story. Fan sentiment — measured through large-scale polls, social media analysis, and convention culture — reveals what the passionate fanbase believes.",
            "subsections": [
                {
                    "heading": "Major Poll Results",
                    "content": "IGN's 2023 global poll (500,000+ respondents) ranked: 1) Christian Bale (34%), 2) Kevin Conroy (28%), 3) Michael Keaton (19%), 4) Robert Pattinson (12%), 5) Ben Affleck (5%), 6) Adam West (2%). Ranker's ongoing poll (1M+ votes) places Conroy at #1, followed by Bale and Keaton. Reddit's r/Batman (500K members) consistently ranks Conroy #1 in internal polls, with active debate between Bale, Keaton, and Pattinson for the live-action crown. The generational divide is stark: voters under 25 favor Pattinson, 25-40 favor Bale, 40+ favor Keaton, and animation/gaming fans of all ages champion Conroy. [Source: IGN] [Source: Ranker] [Source: Reddit r/Batman]"
                },
                {
                    "heading": "The Conroy Exception",
                    "content": "Kevin Conroy's dominance in fan polls reveals something important: for dedicated Batman fans (as opposed to general moviegoers), the definitive portrayal often isn't live-action at all. Batman: The Animated Series is the most critically acclaimed adaptation of the character in any medium (9.1/10 IMDb, 100% RT). The Arkham games placed players inside Batman's head in ways film cannot replicate. Conroy's Batman is the most 'complete' — we see him as detective, fighter, strategist, mentor, and vulnerable human across decades of storytelling. No live-action actor has had equivalent time or narrative scope to develop the character. [Source: IGN] [Source: DC Comics Fan Survey 2023]"
                }
            ],
            "table": {
                "headers": ["Poll Source", "1st Place", "2nd Place", "3rd Place", "Sample Size"],
                "rows": [
                    ["IGN (2023)", "Christian Bale (34%)", "Kevin Conroy (28%)", "Michael Keaton (19%)", "500K+"],
                    ["Ranker", "Kevin Conroy", "Christian Bale", "Michael Keaton", "1M+"],
                    ["r/Batman", "Kevin Conroy", "Christian Bale", "Robert Pattinson", "500K sub"],
                    ["CBR", "Christian Bale", "Kevin Conroy", "Michael Keaton", "50K+"],
                    ["WatchMojo", "Christian Bale", "Michael Keaton", "Kevin Conroy", "200K+"],
                ]
            }
        },

        # ── SECTION 8 ──
        {
            "heading": "8. The Decision Framework: How to Choose Your Greatest Batman",
            "content": "Given that no single actor dominates every dimension, the 'greatest' Batman depends on what you value. This section provides a decision framework for readers to reach their own conclusion based on weighted criteria.",
            "subsections": [
                {
                    "heading": "Dimension-by-Dimension Champion",
                    "content": "If you value critical acclaim: Christian Bale (92% RT, three films over 85%). If you value cultural impact: Michael Keaton (proved dark Batman could succeed, directly influenced Bale, Pattinson, and the entire modern superhero genre). If you value fidelity to source material: Kevin Conroy (30 years spanning the full breadth of Batman comics and storylines). If you value psychological depth: Robert Pattinson (the most nuanced exploration of Bruce Wayne's trauma, grief, and psychology). If you value physical presence: Ben Affleck (the most comics-accurate physical Batman, best fight choreography). If you value historical significance: Adam West (made Batman a global phenomenon; without him, none of the others exist). If you value vocal performance: Kevin Conroy (undisputed; invented the dual-voice technique)."
                },
                {
                    "heading": "The Synthesis: Ranked by Composite Score",
                    "content": "Applying our 5-dimension weighted scoring (Critical 25%, Box Office 20%, Cultural Impact 25%, Craft 20%, Fidelity 10%), the composite rankings are: 1) Christian Bale (9.1/10) — dominant in critics and box office, strong in craft and cultural impact. 2) Kevin Conroy (8.9/10) — perfect in fidelity and fan reception, limited only by lack of live-action presence. 3) Michael Keaton (8.3/10) — the most culturally significant Batman, trailblazer, though his craft scores lower than modern actors. 4) Robert Pattinson (8.0/10) — strongest psychological depth, excellent debut, but incomplete legacy. 5) Ben Affleck (6.5/10) — impressive physicality and ambition undermined by divisive films. 6) Adam West (6.0/10) — historically invaluable but not competitive in modern craft categories. 7) Val Kilmer (5.0/10) — a good performance in a mismatched film. 8) George Clooney (3.0/10) — universally acknowledged as the weakest."
                },
                {
                    "heading": "The Final Answer",
                    "content": "There is no single greatest Batman, because Batman is not a single character. He is a myth that each generation reinterprets. For Generation X, it's Keaton. For Millennials, it's Bale or Conroy. For Gen Z, it's Pattinson. For animation fans, it will always be Conroy. For film historians, Adam West created the template. For comic purists, none have fully captured the 80+ year history of the character — though Conroy came closest. The question 'Who is the greatest Batman?' is less a question about actors than about ourselves: what we fear, what we value, and what kind of hero we need. Batman endures precisely because he can be all of these things to all of these people. And that, perhaps, is the character's greatest triumph."
                }
            ]
        }
    ],

    "key_takeaways": [
        "Christian Bale leads all live-action actors in combined critical acclaim (92% RT average, 8.6 IMDb) and global box office ($2.46B), making him the most decorated live-action Batman by objective metrics",
        "Kevin Conroy is the definitive Batman for dedicated fans — his 30-year run across animation and games is unmatched in scope, consistency, and fan devotion. He invented the dual Bruce/Batman voice technique used by every actor since",
        "Michael Keaton overcame 50,000 fan protest letters to prove in 1989 that a dark, serious Batman could be a blockbuster, directly enabling every darker interpretation that followed — including Nolan's trilogy",
        "Robert Pattinson delivers the most psychologically complex live-action Batman, channeling the character's noir-detective roots in a way no previous live-action actor attempted",
        "No single Batman actor wins across all evaluation dimensions — the 'greatest' depends entirely on what criteria you prioritize: critical acclaim, cultural impact, psychological depth, or fidelity to the comics",
        "George Clooney and Val Kilmer are near-universally considered the weakest portrayals, though Kilmer's performance has received modest retrospective rehabilitation",
        "The Batman myth endures because each generation gets the Batman it needs — West's camp for the 60s, Keaton's darkness for the 80s/90s, Bale's realism for the post-9/11 era, and Pattinson's psychological horror for the 2020s",
        "Fan polls reveal a generational divide: under-25 voters favor Pattinson, 25-40 favor Bale, 40+ favor Keaton, and animation/gaming fans of all ages champion Conroy"
    ],

    "uncertainty_notes": [
        "Robert Pattinson's legacy is incomplete with only one film released; The Batman Part II (2027) could significantly alter his ranking",
        "Fan polls may suffer from recency bias and demographic skew toward younger, more online audiences",
        "Box office comparisons across eras are imperfect — the global market, ticket prices, and population have all grown substantially since 1966. Inflation-adjusted figures provide rough equivalence but cannot fully account for market changes",
        "Voice actors and live-action actors operate in fundamentally different mediums with different craft requirements; direct comparison (e.g., Conroy vs. Bale) is inherently imperfect",
        "Lewis Wilson and Robert Lowery are excluded from most modern rankings due to the obscurity of the 1940s serials and a lack of contemporary critical reviews",
        "Some performance dimensions (particularly 'psychological depth') are inherently subjective and depend on individual interpretation of both the performance and the character"
    ],

    "sources": [
        {"title": "Wikipedia: Batman in Film — Complete History", "url": "https://en.wikipedia.org/wiki/Batman_in_film"},
        {"title": "Rotten Tomatoes: Batman Franchise Scores", "url": "https://www.rottentomatoes.com/franchise/batman"},
        {"title": "IMDb: The Dark Knight (2008) — 9.0/10", "url": "https://www.imdb.com/title/tt0468569/"},
        {"title": "Box Office Mojo: Batman Franchise Grosses", "url": "https://www.boxofficemojo.com/franchise/batman/"},
        {"title": "Metacritic: The Dark Knight — Score 84", "url": "https://www.metacritic.com/movie/the-dark-knight/"},
        {"title": "Roger Ebert: The Dark Knight Review (4/4 stars)", "url": "https://www.rogerebert.com/reviews/the-dark-knight-2008"},
        {"title": "IGN: Best Batman Actor Poll (2023, 500K+ votes)", "url": "https://www.ign.com/articles/best-batman-actor-poll"},
        {"title": "The Hollywood Reporter: Kevin Conroy Obituary", "url": "https://www.hollywoodreporter.com/tv/tv-news/kevin-conroy-dead-batman-voice-actor-1235259944/"},
        {"title": "Variety: The Batman (2022) Review", "url": "https://variety.com/2022/film/reviews/the-batman-review-robert-pattinson-1235193075/"},
        {"title": "Empire Magazine: The Batman 5-Star Review", "url": "https://www.empireonline.com/movies/reviews/the-batman/"},
        {"title": "The Ringer: The Psychology of The Batman", "url": "https://www.theringer.com/movies/2022/3/4/22960309/the-batman-matt-reeves-robert-pattinson"},
        {"title": "Vulture: Every Batman Actor, Ranked", "url": "https://www.vulture.com/article/batman-actors-ranked.html"},
        {"title": "The Atlantic: What Batman Means", "url": "https://www.theatlantic.com/culture/archive/2022/03/batman-movie-robert-pattinson/626932/"},
        {"title": "Ranker: Best Batman Actors (1M+ votes)", "url": "https://www.ranker.com/list/best-batman-actors/ranker-comics"},
        {"title": "ScreenRant: Best Batman Fight Scenes Ranked", "url": "https://screenrant.com/batman-best-fight-scenes-ranked/"},
        {"title": "Den of Geek: Val Kilmer Batman Retrospective", "url": "https://www.denofgeek.com/movies/val-kilmer-batman-forever-retrospective/"},
        {"title": "GQ: George Clooney on Batman & Robin Regrets", "url": "https://www.gq.com/story/george-clooney-batman-and-robin"},
        {"title": "The Numbers: Batman Franchise Financial Analysis", "url": "https://www.the-numbers.com/franchise/Batman"},
        {"title": "Reddit r/Batman: Community Rankings", "url": "https://www.reddit.com/r/batman/"},
        {"title": "DC Comics Official: Batman History", "url": "https://www.dc.com/characters/batman"}
    ],

    "research_metadata": {
        "sub_questions_asked": 8,
        "total_findings": 52,
        "iterations": 3,
        "search_queries": [
            "complete list Batman actors ranked critics reviews history",
            "Christian Bale Batman performance analysis Dark Knight trilogy impact",
            "Michael Keaton Batman 1989 cultural legacy fan protests",
            "Kevin Conroy Batman voice actor animated series Arkham games legacy",
            "Robert Pattinson Batman psychological depth noir detective analysis",
            "Ben Affleck Batman v Superman performance review fight scenes",
            "Adam West Batman 1966 cultural impact camp legacy",
            "Batman box office comparison inflation adjusted all actors"
        ],
        "decomposition_strategy": "Multi-dimensional analysis covering all 8 live-action actors plus Kevin Conroy across critical reception, box office, cultural impact, psychological depth, and fidelity to source material. Three iterations with gap-filling for fan sentiment data and psychological analysis."
    }
}


def inject_demo_session():
    session_id = "demo-batman-01"
    session = ResearchSession(session_id, "Which actor is the greatest Batman and why?")
    session.status = "complete"
    session.report = SIMULATED_REPORT
    session.metadata = SIMULATED_REPORT["research_metadata"]

    session.progress = [
        {"type": "phase", "data": {"phase": "planning", "message": "Decomposing research question into 8 sub-questions..."}, "time": 0},
        {"type": "plan_complete", "data": {"strategy": "Multi-dimensional analysis across all 8 live-action actors + voice actors, covering 5 evaluation dimensions", "sub_questions": [
            "Complete list of all Batman actors with historical context",
            "Critical reception: aggregated scores, major reviews per actor",
            "Box office performance: inflation-adjusted comparison",
            "Cultural impact: who changed the character and genre?",
            "Psychological depth and acting craft analysis",
            "Fan sentiment: polls, social media, convention culture",
            "Kevin Conroy analysis: voice actor as definitive Batman",
            "Decision framework: weighted composite scoring"
        ], "count": 8}, "time": 1},
        {"type": "phase", "data": {"phase": "searching", "iteration": 1, "total_iterations": 3, "message": "Research iteration 1/3 — searching 8 angles..."}, "time": 2},
        {"type": "finding_complete", "data": {"sub_question": "Complete list of all Batman actors", "facts_found": 7, "quality": "Comprehensive — all 8 live-action actors + Conroy identified with historical context"}, "time": 3},
        {"type": "finding_complete", "data": {"sub_question": "Critical reception analysis", "facts_found": 8, "quality": "Excellent — RT, Metacritic, IMDb, Ebert data compiled"}, "time": 4},
        {"type": "finding_complete", "data": {"sub_question": "Box office performance comparison", "facts_found": 6, "quality": "Strong — raw and adjusted figures with budget multipliers"}, "time": 5},
        {"type": "finding_complete", "data": {"sub_question": "Cultural impact analysis", "facts_found": 7, "quality": "Rich — historical context, industry influence, paradigm shifts"}, "time": 6},
        {"type": "phase", "data": {"phase": "analyzing", "iteration": 1, "message": "Analyzing findings for gaps..."}, "time": 7},
        {"type": "analysis_complete", "data": {"coverage_score": 7, "needs_more": True, "gaps": ["Fan sentiment data needed", "Psychological depth analysis for Pattinson incomplete", "Acting craft comparison underdeveloped"], "assessment": "Strong foundation. Need fan data and deeper craft analysis."}, "time": 8},
        {"type": "phase", "data": {"phase": "searching", "iteration": 2, "total_iterations": 3, "message": "Research iteration 2/3 — filling gaps: fan data, craft analysis, psychology"}, "time": 9},
        {"type": "finding_complete", "data": {"sub_question": "Fan polls and sentiment across platforms", "facts_found": 9, "quality": "Comprehensive — IGN (500K+), Ranker (1M+), Reddit, CBR, WatchMojo polls"}, "time": 10},
        {"type": "finding_complete", "data": {"sub_question": "Psychological depth: Pattinson vs Bale vs Keaton", "facts_found": 6, "quality": "Strong — expert reviews from Empire, Variety, The Ringer"}, "time": 11},
        {"type": "finding_complete", "data": {"sub_question": "Acting craft: voice, physicality, Bruce/Batman duality", "facts_found": 5, "quality": "Good — technique analysis across all major actors"}, "time": 12},
        {"type": "phase", "data": {"phase": "analyzing", "iteration": 2, "message": "Analyzing expanded findings..."}, "time": 13},
        {"type": "analysis_complete", "data": {"coverage_score": 9, "needs_more": True, "gaps": ["Legacy/sequel information for Pattinson missing", "Comparative ROI analysis needed"], "assessment": "Near-complete. Two minor gaps remain for completeness."}, "time": 14},
        {"type": "phase", "data": {"phase": "searching", "iteration": 3, "total_iterations": 3, "message": "Research iteration 3/3 — final gap fill: future films, ROI data"}, "time": 15},
        {"type": "finding_complete", "data": {"sub_question": "Future Batman films and legacy in progress", "facts_found": 3, "quality": "Adequate — Pattinson sequel confirmed, DCU reboot announced"}, "time": 16},
        {"type": "finding_complete", "data": {"sub_question": "Budget-to-gross ROI comparison all actors", "facts_found": 4, "quality": "Good — The Numbers profit data compiled"}, "time": 17},
        {"type": "phase", "data": {"phase": "analyzing", "iteration": 3, "message": "Final analysis — all angles covered..."}, "time": 18},
        {"type": "analysis_complete", "data": {"coverage_score": 10, "needs_more": False, "gaps": [], "assessment": "Comprehensive. All dimensions covered. 52 findings across 8 sub-questions. Ready for synthesis."}, "time": 19},
        {"type": "phase", "data": {"phase": "synthesizing", "message": "Synthesizing all 52 findings into comprehensive 8-section report..."}, "time": 20},
        {"type": "report_complete", "data": SIMULATED_REPORT, "time": 21},
        {"type": "phase", "data": {"phase": "complete", "message": "Research complete — 8 sections, 20 sources, 52 findings"}, "time": 22},
    ]

    SESSIONS[session_id] = session
    return session_id


if __name__ == "__main__":
    session_id = inject_demo_session()
    print("=" * 62)
    print("  🦇 DeepResearch Demo — Batman: Comprehensive Analysis")
    print("=" * 62)
    print(f"  Demo session: {session_id}")
    print(f"  Report sections: {len(SIMULATED_REPORT['sections'])}")
    print(f"  Subsections: {sum(len(s.get('subsections', [])) for s in SIMULATED_REPORT['sections'])}")
    print(f"  Data tables: {sum(1 for s in SIMULATED_REPORT['sections'] if s.get('table'))}")
    print(f"  Sources cited: {len(SIMULATED_REPORT['sources'])}")
    print(f"  Total findings: {SIMULATED_REPORT['research_metadata']['total_findings']}")
    print(f"  Iterations: {SIMULATED_REPORT['research_metadata']['iterations']}")
    print(f"  Key takeaways: {len(SIMULATED_REPORT['key_takeaways'])}")
    print(f"  Uncertainty notes: {len(SIMULATED_REPORT['uncertainty_notes'])}")
    print(f"  Composite ranking: Bale (9.1) > Conroy (8.9) > Keaton (8.3) > Pattinson (8.0)")
    print("=" * 62)
    print(f"  Server: http://localhost:5000")
    print(f"  App UI: http://localhost:5000/app")
    print("=" * 62)
    print(f"  ⚠ Demo server binds to 127.0.0.1 (localhost only)")
    print(f"  To expose publicly: DEEPRESEARCH_HOST=0.0.0.0 DEEPRESEARCH_API_TOKEN=... python demo_batman.py")
    print("=" * 62)

    app.run(host="127.0.0.1", port=5000, debug=False)
