# Chapter 25 — Five Approaches to Context Management

> **The bug wasn't in the model. It was in what the model couldn't stop seeing.**

This is the demo repo for Chapter 25 of *Design of Agentic Systems with Case Studies*.

**Core claim:** The locus of control for context curation determines the failure mode of a long-running agent — not the size of the context window. Not the model. Not the prompt. The architecture.

---

## What's in here

```
Chapter25_Scenario_Context_Management.md   ← full chapter prose (9 sections)
Chapter25_Pedagogical_Audit.md            ← Eddy the Editor audit (13 flags)
authors_note.md                           ← 3-page pedagogical report
ch25_notebook.ipynb                       ← full demo notebook (13 cells)
ch25_notebook_results.ipynb               ← pre-executed results
passive_agent.py                          ← standalone passive agent (runnable)
acm_agent.py                              ← standalone ACM agent (runnable)
README.md                                 ← this file
```

---

## The scenario

Archer is a coding agent given one task: find and fix an intermittent 401 error on a token-refresh endpoint. The bug occurs 1-in-40 sessions, always under load, never in staging.

Archer spends 5 hours on it. At 3pm it delivers a confident patch. The patch modifies the Redis lock TTL — the exact parameter that Archer's own investigation had already ruled out 3 hours earlier.

The context window was at 40% capacity. No token budget error. No crash. The agent just couldn't stop seeing its own dead-end.

That's context rot. And it's not a model problem.

---

## The five approaches

| Approach | Who curates | Failure mode | Failure visible? |
|---|---|---|---|
| Passive truncation | Nobody | Accumulation — stale tokens persist forever | No |
| Compaction-on-threshold | Engine (oldest-first) | Semantic blindness — compacts constraints, keeps noise | No |
| RLM | Model (once, at init) | Problem mismatch — batch architecture on a streaming problem | No |
| LCM | Engine (DAG traversal) | Semantic blindness by exclusion — lossless ≠ relevant | No |
| ACM | Model (continuously) | Metacognitive error — model removes what it needs | **Yes** |

ACM's failure mode is the only one that's auditable. That asymmetry is the chapter's argument.

---

## Quickstart — no Jupyter needed

Requires Python 3.8+, no external packages.

```bash
git clone https://github.com/DevanshuNEU/agentic-context-management.git
cd agentic-context-management

# Run the passive agent — watch vocab contamination accumulate, get wrong answer
python3 passive_agent.py

# Run the ACM agent — same task, same injected dead-ends, correct answer
python3 acm_agent.py
```

Both scripts use only Python stdlib (`dataclasses`, `typing`). No pip install required.

---

## Jupyter notebook demo

For the full 13-cell demo with vocabulary drift charts and side-by-side comparison:

```bash
jupyter notebook ch25_notebook.ipynb
```

**Run cells 1–7** → passive agent, vocabulary contamination bar chart.

**Cell 8** → MANDATORY HUMAN DECISION NODE. `raise NotImplementedError` hard stop. Set `YOUR_DECISION = "proactive"` and document reasoning before proceeding.

**Run cells 9–13** → ACM agent, comparison table, failure mode demonstration.

Pre-executed results are in `ch25_notebook_results.ipynb`.

---

## The exercise

After running both agents, answer this before checking output:

> At what turn do the two agents diverge? What specific tokens are present in the passive agent's context and absent from the ACM agent's context at that turn? Trace the attention sink mechanism to the output divergence.

**Answer that fails:** "The ACM agent did better because it managed context."

**Answer that passes:** "At turn 6, the passive agent's context contained 12 instances of dead-end vocabulary (`pool_exhaustion`, `connection_pool`, etc.) from the turn-5 injection, creating an attention sink that biased turns 6–18 toward the wrong hypothesis. The ACM agent's context view contained a 2-line tombstone — the attention sink never formed because `remove_context` fired at the moment of invalidation."

---

## Human Decision Node

Cell 8 of the notebook is a hard stop (`raise NotImplementedError`). The decision documented:

> The scaffold proposed **reactive** removal — `remove_context` fires when context is crowded. I rejected this because the architectural argument is about **timing**, not just tool availability. Proactive removal (at moment of invalidation) prevents the attention sink from forming. Reactive removal cleans it up after damage is done. Those are not equivalent. The divergence table proves it: proactive ACM peak vocabulary = 13, passive peak = 37.

This rejection is visible in the notebook, documented in `authors_note.md` Page 2, and stated on camera in the video.

---

## Key lines from the chapter

- *"A session can be at forty percent of its token budget and be ninety percent corrupted by stale reasoning. Those two numbers are not related."*
- *"Recoverability and relevance are orthogonal properties. LCM optimizes the first and does not touch the second."*
- *"The log is a ledger; the view is a query result."*
- *"Architecture that produces auditable failures is architecture that can be supervised, corrected, and improved. Architecture that produces silent failures can only be replaced."*

---

## Built with

- **Bookie the Bookmaker** — prose generation, Tetrahedron structuring
- **Eddy the Editor** — pedagogical audit (13 flags, corrections documented in `authors_note.md`)
- **Chapter type:** C (Framework/Approach Evaluation)
- **Core claim:** *"After reading this chapter, a student will understand how the locus of control for context curation determines the failure mode of a long-running agent well enough to select the right context management architecture for a given workload without making the mistake of treating context overflow as a capacity problem solvable by a larger context window."*

*Devanshu Chicholikar — MS Software Engineering Systems, Northeastern University*
