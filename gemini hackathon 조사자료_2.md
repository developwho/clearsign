# Your complete guide to winning the Gemini 3 Seoul hackathon

**The Cerebral Valley × Google DeepMind Gemini 3 hackathon series is one of the largest AI hackathon tours ever staged**, spanning 12+ events across 7 cities on 3 continents from September 2025 through March 2026. For the Seoul stop on February 28, the pattern is clear: judges reward **multimodal, agentic projects that solve real human problems** — not chatbots, not basic RAG, and not prompt wrappers. The official judging formula weights Technical Execution at **40%**, Innovation at **30%**, Impact at **20%**, and Demo quality at **10%**. Below is everything publicly known about what winning looks like, drawn from completed events in San Francisco, New York, London, Bengaluru, and Tokyo.

---

## The full scope of the Gemini 3 hackathon series

Cerebral Valley — the SF-born AI community with **40,000+ builders** in its network — has partnered with Google DeepMind and the **AI Futures Fund** to run a global hackathon circuit. The series evolved through several phases:

| Event | Date | City | Focus | Prizes |
|-------|------|------|-------|--------|
| Nano Banana Hackathon | Sep 6, 2025 | San Francisco | Gemini 2.5 Flash image generation | $50K+ API credits |
| TED AI Hackathon | Oct 18–19, 2025 | San Francisco | Agentic multimodal apps | $6K cash + $50K credits |
| Vibe Code Hackathon | Nov 8, 2025 | San Francisco | Rapid prototyping in AI Studio | $100K API credits |
| Vibe Code Hackathon | Nov 15, 2025 | London | Rapid prototyping in AI Studio | $100K API credits |
| AIE Code Agents Hack | Nov 22–23, 2025 | New York | Code agents (first Gemini 3 event) | $6K+ cash + $150K credits |
| Gemini 3 Hackathon | Dec 6, 2025 | San Francisco | Open-ended Gemini 3 builds | $150K credits + AI Futures Fund call |
| Gemini 3 Hackathon | Dec 13, 2025 | London | Open-ended Gemini 3 builds | $150K credits + AI Futures Fund call |
| Gemini 3 SuperHack | Jan 31, 2026 | San Francisco | Sports & live entertainment | $150K+ credits + partner prizes |
| APAC Tour: Bengaluru | Feb 14, 2026 | Bengaluru, India | Open-ended Gemini 3 | $150K credits + AI Futures Fund call |
| APAC Tour: Tokyo | Feb 21, 2026 | Tokyo (Shibuya) | AI for Gaming (with Supercell) | ~¥24M credits + AI Futures Fund call |
| APAC Tour: Seoul | Feb 28, 2026 | Seoul, Korea | Production Sprint with AttentionX | ₩221M (~$150K) credits + AI Futures Fund call |
| APAC Tour: Singapore | Mar 7, 2026 | Google Developers Space | Defined 5-track format | $100K credits + AI Futures Fund call |
| Global Online Hackathon | Dec 17–Feb 9 | Devpost (virtual) | 4 tracks, open-ended | $100K cash ($50K grand prize) |

Every in-person event follows a **single-day, 13-hour format** (9 AM–10 PM local time), with a maximum team size of **4 people**, application-based admission, and fully in-person attendance required. The SF event attracted **100+ builders**, and other events likely drew similar curated crowds of 50–150 participants. The London event gallery confirmed both **judge-selected winners** and **community vote winners**, suggesting a dual-track awards system.

---

## Judging criteria: technical execution dominates at 40%

The official judging rubric from the Devpost global hackathon — which the in-person events closely mirror — breaks down as follows:

**Technical Execution (40%)** evaluates quality of development, how deeply you leverage Gemini 3's capabilities, and whether the code is functional. This is the heaviest weight by far. **Innovation / Wow Factor (30%)** asks whether the idea is novel and original, whether it addresses a significant problem in a unique way. **Potential Impact (20%)** measures real-world utility, market breadth, and the significance of the problem being solved. **Presentation / Demo (10%)** covers problem definition clarity, effective demonstration, architectural documentation, and explanation of Gemini 3 integration.

The process is two-stage: first a pass/fail viability check (did you meet submission requirements and reasonably address a challenge?), then weighted scoring. For in-person events, Cerebral Valley uses a **Gavel judging system** — pairwise comparison — to select **top 6 finalists** who demo to the full judge panel.

The Singapore event revealed a detailed prize breakdown that likely mirrors Seoul's structure: **Best Overall** (30,000 credits) for technical excellence plus real-world utility; **Best Execution** (20,000 credits); **Best Technical Implementation** (10,000 credits); **5 Specialist Awards** (6,000 credits each) for categories like Best Use of Audio, Best Agentic Workflow, and Best UI/UX; and **Most Creative** (10,000 credits) for "weird but wonderful" projects.

---

## What Google explicitly does not want you to build

The Devpost resources page is blunt about what will fail. Google calls this the **"Action Era"** and warns: *"If a single prompt can solve it, it is not an application."*

Projects that judges will immediately deprioritize include **baseline RAG** (Gemini 3's verified 1M-token context window makes simple retrieval a commodity feature), **prompt-only wrappers** in basic UI, **simple vision analyzers** doing basic object identification, **generic chatbots** for nutrition, job screening, or personality analysis, and any project generating **medical diagnostic advice**. These anti-patterns represent the majority of typical hackathon submissions — avoiding them already puts you ahead.

---

## Winning project patterns from the broader Gemini ecosystem

While specific winner names from Cerebral Valley's in-person events are locked behind authenticated project galleries on cerebralvalley.ai, extensive data exists from Google's official competitions and related hackathons. These patterns are highly instructive.

**The most consistent winner archetype is an accessibility or assistive technology tool using multimodal AI.** In Google's Gemini API Developer Competition, **VITE VERE** won both Most Impactful and People's Choice by helping people with cognitive disabilities achieve independence through Gemini's visual understanding — the model watches what users are doing and provides personalized step-by-step instructions. **Gaze Link** won Best Android App by combining eye-tracking with Gemini to help ALS patients communicate. **ViddyScribe** won Best Web App by automatically generating audio descriptions for videos to assist blind users.

The Best Overall App winner, **Jayu**, exemplifies what judges reward most: a system-level AI agent that integrates into the user's OS, interprets visual information from any application, interacts with app interfaces via function calling, and performs real-time translation. It used **3+ Gemini features in concert** — vision, function calling, and real-time processing.

At a previous Cerebral Valley hackathon, **Open Glass** won first place with **$20 open-source smart glasses** built in 24 hours — 3D printed frames with a camera and mic connected to Gemini. Despite a bug during the live demo, judges (including Hugging Face CEO Clem Delangue and Meta/Groq executives) awarded it first place. The project generated **1,500 preorders within hours**. The lesson: judges value vision and market traction over flawless execution.

In the GKE Turns 10 hackathon, winning projects featured **multi-agent architectures** with 4–6 specialized agents. **Vigil AI** deployed a hierarchical fraud detection system with 4 specialized agents. **Cartmate** used 6 specialized AI shopping agents. These multi-agent patterns align precisely with what the Gemini 3 series emphasizes.

---

## Five tracks that define where winners emerge

The Singapore event listed explicit tracks that likely reflect the Seoul framework:

**SOTA Reasoning & Multimodality** challenges builders to use Gemini's 1M+ context window to ingest, analyze, and reason across text, images, audio, and video simultaneously — extracting "high-fidelity facts from complex, messy real-world data." **Agentic Coding** goes beyond autocomplete to build agents that refactor legacy codebases, architect new systems, or autonomously debug complex errors. **GenMedia** leverages Gemini TTS, Lyria (music), Nano Banana (images), and Veo (video) for creative applications. **Deep Research & Interactions API** builds recursive investigation tools that browse, read, synthesize, and report on vast knowledge. **Advanced Tool Use & Planning** focuses on function calling — building agents that take real-world actions.

The global Devpost hackathon used slightly different naming: **Marathon Agent** (autonomous multi-step systems spanning hours), **Vibe Engineering** (rapid prototyping via AI Studio's Build tab), **Real-Time Teacher** (using Gemini Live API), and **Creative Autopilot** (image generation plus reasoning).

Google's example inspirations reveal the ambition level expected: a **"Legacy Lifter"** that refactors COBOL codebases into modern Go/Rust with unit tests, a **"Security Sentinel"** that scans repos for vulnerabilities and opens fix PRs, a **"Text-to-SaaS"** system that deploys functional prototypes from natural language, and a **"Black Box Decoder"** that reads server logs and screen recordings to pinpoint crash causes.

---

## Technical stack: what winners actually use

The Gemini 3 hackathons require building on **three platforms**: Google AI Studio (fastest prototyping), Vertex AI (enterprise deployment), and **Antigravity** — Google's new agentic development platform. Using Antigravity signals to judges that you're leveraging cutting-edge tools.

Winners consistently use **multiple Gemini capabilities in combination** rather than a single API call. The most impactful technical patterns include multimodal vision and understanding (nearly universal among winners), **function calling and tool use** (dominant in agent-based winners), the **Live API** for real-time streaming interactions, **Google Search grounding** for factual accuracy, the **Agent Development Kit (ADK)** for multi-agent orchestration, and **A2A protocols** for agent-to-agent communication.

Critical Gemini 3 technical details to master: keep **temperature at the default 1.0** (Gemini 3 is optimized for it), use the **`thinking_level` parameter** (high for complex reasoning, low for speed), and handle **Thought Signatures** correctly — these encrypted reasoning representations are required for function calling, and missing them produces 400 errors. Control media quality with `media_resolution` (low/medium/high/ultra_high) to balance quality against token cost. For prompting, be direct and skip elaborate chain-of-thought instructions — Gemini 3 handles reasoning internally.

---

## Strategic playbook for the Seoul hackathon

### Before February 28

**Form a team of exactly 4** — maximize your allowed size. The ideal composition: one strong backend/API engineer, one frontend/UX person, one AI/ML specialist comfortable with Gemini's API surface area, and one person dedicated to pitch and demo preparation. **Pre-plan 2–3 project ideas** targeting different tracks so you can pivot within the first hour. Master AI Studio's Build tab for rapid prototyping, set up your Gemini API key, and experiment with Thought Signatures, function calling, and multimodal inputs before the event.

### What to build

Build **agentic, not conversational**. Google is emphatic that this is the Action Era. Build agents that plan, execute, use tools, and handle multi-step workflows autonomously. Go **multimodal** — projects leveraging multiple input types (text, images, audio, video, code) consistently score higher than text-only apps. Solve a **real human problem** — accessibility and education projects win disproportionately across all Gemini hackathons.

**Leverage Korea-specific angles.** AttentionX, one of Korea's most prominent AI startup accelerators, is co-hosting. Consider problems relevant to the Korean market or showcasing Korean-language capabilities. The Seoul event is described as a **"Production Sprint"** — you must deploy an actually functioning application, not just pitch a concept.

Use Gemini's **1M-token context window creatively** — process entire codebases, long documents, or hours of video. This is a differentiated capability that impresses judges. Incorporate **spatial reasoning** for screen understanding or trajectory prediction. These are cutting-edge Gemini capabilities that demonstrate deep technical integration.

### Demo strategy that wins

Lead with the most impressive capability in the **first 60 seconds** — judges may not watch beyond 3 minutes. Start with the problem (make judges feel the pain), then show the solution working live. Include an **architectural diagram** (explicitly called out in judging criteria) and a clear **200-word explanation** of which Gemini 3 features you use and why they're central. Make your demo publicly accessible — ideally via AI Studio apps requiring no login.

The single most important demo principle from past winners: **show what's different, not just what's good.** Every hackathon project is competent. Winners demonstrate what they do that nobody else can. Open Glass won by physically wearing $20 glasses on stage. Outdraw AI won Most Creative by making AI an opponent in a party game. Your demo needs one unforgettable moment.

### The hidden prize worth more than credits

The **30-minute virtual call with AI Futures Fund founders** may be the most valuable prize offered. The Fund makes rolling, thesis-driven investments from seed to late stage, offering equity investment plus early access to DeepMind models and collaboration with Google experts. Their portfolio includes companies like Viggle (AI meme-making), Toonsutra (digital comics), and Rooms (interactive 3D spaces). Frame your project as the **seed of a viable startup**, not just a hackathon toy. This single call could be worth more than any amount of API credits.

---

## Conclusion: what winning actually looks like

Across the entire Gemini hackathon ecosystem, a clear winner profile emerges. The winning project uses **3+ Gemini capabilities in concert** (multimodal input, function calling, grounding, or generation). It solves a **specific, emotionally resonant human problem** — not an abstract technical challenge. It features **one unforgettable demo moment** that judges will remember when comparing projects. It demonstrates **agent-level autonomy** — planning, executing, and self-correcting across multiple steps. And it looks like the **beginning of a real product**, not a weekend experiment.

The projects that lose are the ones Google explicitly warned against: chatbots, basic RAG, prompt wrappers, and simple vision classifiers. With 40% of the score riding on Technical Execution, the depth of your Gemini 3 integration matters enormously — surface-level API calls won't compete against teams chaining Thought Signatures, function calling, multimodal reasoning, and tool use into coherent agent workflows. But technical depth alone isn't enough. The 30% Innovation weight means you need a genuinely novel angle. And the 20% Impact weight means judges want to believe your project could matter beyond the hackathon.

For Seoul specifically: the Production Sprint format means you must ship a working, deployed application in 13 hours. Scope ruthlessly. A polished, focused demo of one powerful capability beats an ambitious but broken prototype every time.