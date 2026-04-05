# Chapter 25 — Five Approaches to Context Management

> **The bug wasn't in the model. It was in what the model couldn't stop seeing.**

This is the demo repo for Chapter 25 of *Design of Agentic Systems with Case Studies*.

The chapter makes one architectural argument: **the locus of control for context curation determines the failure mode of a long-running agent — not the size of the context window.**

Not the model. Not the prompt. The architecture.

---

## What's in here

```
Chapter25_Scenario_Context_Management.md   ← the full chapter (9 sections)
ch25_notebook.ipynb                        ← runnable demo
ch25_notebook_results.ipynb               ← results with outputs
Chapter25_Pedagogical_Audit.md            ← Eddy the Editor's audit (13 flags)
authors_note.md                           ← 3-page pedagogical report
```

---

## The scenario

Archer is a coding agent. It's given one task: find and fix an intermittent 401 error on a token-refresh endpoint. The bug occurs 1-in-40 sessions, always under load, never in staging.

Archer spends 5 hours on it. At 3pm it delivers a confident patch. The patch modifies the Redis lock TTL — the exact parameter that Archer's own investigation had already ruled out 3 hours earlier.

The context window was at 40% capacity. No token budget error. No crash. The agent just couldn't stop seeing its own dead-end.

That's context rot. And it's not a model problem.

---

## The five approaches

| Approach | Who curates | Failure mode | Visible? |
|---|---|---|---|
| Passive truncation | Nobody | Accumulation — stale tokens persist forever | No |
| Compaction-on-threshold | Engine (oldest-first) | Semantic blindness — compacts constraints, keeps noise | No |
| RLM | Model (once, at init) | Problem mismatch — batch architecture on a streaming problem | No |
| LCM | Engine (DAG traversal) | Semantic blindness by exclusion — lossless ≠ relevant | No |
| ACM | Model (continuously) | Metacognitive error — model removes what it needs | **Yes** |

ACM's failure mode is the only one that's auditable. That asymmetry is the chapter's argument.

---

## Running the demo

Open `ch25_notebook.ipynb` in Jupyter or Colab. No external API needed — the stub tool environment simulates everything.

```bash
jupyter notebook ch25_notebook.ipynb
```

**Run cells 1–7** to see the passive agent accumulate vocabulary contamination and fail to find the bug.

**Stop at Cell 8.** This is the Human Decision Node. Document your decision before proceeding.

**Run cells 9–13** to see the ACM agent remove dead-ends at the moment of invalidation and find the correct answer.

---

## The exercise

After running both agents, answer this before checking the comparison output:

> At what turn do the two agents diverge? What specific tokens are present in the passive agent's context and absent from the ACM agent's context at that turn? Trace the attention sink mechanism to the output divergence you observe.

The answer that passes: names the turn, names the tokens, traces the causal chain.

The answer that doesn't: "the ACM agent did better because it managed context."

---

## Key lines from the chapter worth keeping

- *"A session can be at forty percent of its token budget and be ninety percent corrupted by stale reasoning. Those two numbers are not related."*
- *"Recoverability and relevance are orthogonal properties. LCM optimizes the first and does not touch the second."*
- *"The log is a ledger; the view is a query result."*
- *"Architecture that produces auditable failures is architecture that can be supervised, corrected, and improved. Architecture that produces silent failures can only be replaced."*

---

## Built with

- Bookie the Bookmaker — prose generation and Tetrahedron structuring
- Eddy the Editor — pedagogical audit (13 flags, 5 accepted corrections, 3 rejected with reasoning)
- PostHog-style directness — start with the point, show the failure, don't hide the cost

*Devanshu Chicholikar — MS Software Engineering Systems, Northeastern University*
