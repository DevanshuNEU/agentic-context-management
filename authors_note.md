# Author's Note — Chapter 25: Five Approaches to Context Management

*Devanshu Chicholikar | MS Software Engineering Systems, Northeastern University*

---

## Page 1 — Design Choices

I picked context management because I've been burned by it.

Not dramatically. In the way where you run an agent for 20 minutes, get back a confident answer, ship the fix, and then spend another hour figuring out why it didn't work. The agent wasn't wrong in any obvious sense. Its reasoning was coherent. Its output was well-formatted. It just happened to be answering a slightly different question than the one you asked — one shaped by dead-end vocabulary from 45 minutes ago that never left its context.

That's the failure this chapter is about. And the reason I spent time on it is that most engineers I've seen encounter this and misattribute it. They think the model hallucinated. They think the prompt was bad. They scale up to a better model. None of those fix it, because none of those touch the actual problem: the architecture of who controls context curation.

**The book's master argument is that architecture is the leverage point, not the model.** My chapter is a specific instance: the locus of control for context curation is an architectural decision, and it determines the failure mode. A better model attending to a contaminated context produces better-written wrong answers. The intervention has to be at the architectural layer.

**My chapter's core claim sentence:**
> *"After reading this chapter, a student will understand how the locus of control for context curation determines the failure mode of a long-running agent well enough to select the right context management architecture for a given workload without making the mistake of treating context overflow as a capacity problem solvable by a larger context window."*

The Z — the mistake the chapter prevents — is treating context rot as a token budget problem. It isn't. Archer's session at 1:30 PM was at 40% of its token budget. The failure was semantic, not structural.

I anchored everything to Archer because abstract systems explanations fail when they don't make the failure visceral. The 9:47 AM start time, the 3:00 PM wrong patch, the specific token counts (11x `lock_acquired_at`, 19x `timestamp`) are doing real work. They let a reader feel the drift before they understand the mechanism.

**What I left out deliberately:**

Hybrid approaches — ACM layered on top of LCM — are real and probably more robust than either alone. I excluded them because the chapter's job is to make the design decision legible. Once you understand why ACM and LCM make different bets, you can compose them. Teaching the composition before the bets are clear produces confusion.

Fine-tuning for metacognitive accuracy is the obvious next question after ACM. I excluded it because that's a training-time intervention and this chapter is about inference-time architecture. They're different levers.

The interaction between context management strategy and model capability — smaller models may need more aggressive proactive removal because metacognitive accuracy is lower — I excluded because quantifying it requires empirical data I don't have, and I'd rather be honest about the gap than speculate.


---

## Page 2 — Tool Usage

**Bookie — what it got right and where I corrected it**

Bookie generated strong prose throughout. The Archer scenario came back nearly publication-ready on the first pass. The Tetrahedron structure applied consistently across all five approaches is Bookie's work — I directed it, but it executed the parallel structure cleanly.

The corrections matter more than the generation:

**Correction 1 — KV cache mechanism framing (REJECTED, then corrected)**
Bookie's first draft of the Scenario Tetrahedron Read wrote:
> *"attention mechanisms weight tokens partly by position and partly by learned relevance patterns."*

That's vague. The real mechanism is attention sink behavior driven by KV cache persistence — dead-end tokens remain in the KV cache and are attended to on every forward pass, and softmax normalization means high-salience tokens win attention budget at the expense of everything else. I corrected this and moved the mechanistic language out of the Scenario section entirely, replacing it with a forward reference. The mechanism section now earns the claims the Scenario section makes. This correction is the Human Decision Node for the prose phase.

**Correction 2 — RLM benchmark claim (REJECTED)**
Bookie cited RLM's performance as "two orders of magnitude beyond model context windows" without sourcing the claim. I traced it to secondary analysis (Dead Neurons Substack) rather than Zhang, Kraska, Khattab (2026) directly. I kept the claim but scoped it as secondary-sourced. I can't argue against benchmark selection bias in the RLM section while uncritically accepting an unsourced benchmark figure.

**Correction 3 — ACM promissory note (REJECTED)**
Bookie wrote: *"This is the dimension on which ACM will improve as models improve."*
That's a forward-looking claim with no grounding. I replaced it with: metacognitive error rates in ACM-style deployments aren't yet well-measured in published literature, and an engineering team adopting ACM should instrument the error rate from first deployment. The comparison is currently between a known error rate (ACM's auditable failures) and an unknown one (passive's silent failures). That asymmetry is the architectural argument — but it's not evidence that ACM's error rate is zero.

**Eddy the Editor — 13 flags, what I accepted and what I pushed back on**

*Accepted (5):*
- KV cache language before mechanism existed → replaced with forward reference
- Softmax undefined in mechanism section → added one sentence: softmax converts raw scores to weights that sum to 1.0, so stronger scores win a larger share of a fixed attention budget
- DAG undefined on first use → added parenthetical: "directed acyclic graph: a structure with no cycles, so every compaction pass is guaranteed to terminate"
- ACM metacognitive error rate ungrounded → corrected as above
- Position-based selection criterion not traced to design decision → added: changing the criterion to "least semantically relevant" would require calling the model, which changes the architecture from engine-driven to model-participatory — that's not a tweak, it's a different approach

*Rejected — Failure 11 (LCM strengths front-loaded):*
Eddy wanted: strengths → infrastructure cost → failure mode. I kept: strengths → failure mode → infrastructure cost. Reason: this mirrors how a practitioner evaluates a system — credit before critique. Reordering creates a false impression that LCM is bad engineering. It isn't. It's well-engineered with the wrong problem.

*Rejected — Failure 12 (benchmark meta-critique):*
Eddy wanted a full paragraph on how benchmark selection is standard practice in architecture papers. I added the one sentence about benchmarks chosen to demonstrate fit-for-purpose, not general superiority. I didn't add the full meta-critique because it would shift the RLM section from context management architecture to AI evaluation methodology — out of scope.

*Rejected — Failure 6 (KV entry phrasing):*
Eddy flagged: *"the attention computation weighted both sets of KV entries"* as conflating keys and values. Eddy's proposed fix was: *"The query vectors at the current position produced high dot-product scores against both sets of key vectors, pulling the weighted sum of value vectors toward both framings simultaneously."* I initially noted this as a rejection, but on reflection this correction is mechanistically more precise and consistent with the mechanism section. I accepted it. This is documented as a correction, not a rejection.

**Human Decision Node — Demo (Cell 8)**
The scaffold proposed reactive ACM — `remove_context` fires when context pressure builds. I rejected this because the architectural argument is about *timing*, not just tool availability. Proactive removal at moment of invalidation prevents the attention sink from forming. Reactive removal cleans up after damage is done. The divergence table (turn 6: passive=12 tokens, ACM=10; turn 19: passive=37, ACM=13) proves the difference is architectural, not incidental.


---

## Page 3 — Self-Assessment

**Scoring against the rubric:**

*Architectural Rigor (35 pts) — self-score: 32/35*

The chapter identifies the failure mode (context rot), traces the causal chain (stale KV cache entries → high dot-product scores → biased value-weighted sum → wrong output), and demonstrates the failure triggered and observed in two runnable files. The five-approach comparison credits LCM's genuine strengths before naming its limitation, and ACM's failure mode is demonstrated explicitly (Cell 13, `remove_context` without prior `pin()`). The half-point gap: I don't have empirical data on metacognitive error rates in production ACM deployments, so the comparison between ACM and passive is partly structural argument rather than measured evidence.

*Technical Implementation (25 pts) — self-score: 23/25*

The notebook runs end-to-end. `passive_agent.py` and `acm_agent.py` run with `python3` from a fresh clone — no external packages. Human Decision Node is a hard `raise NotImplementedError` in Cell 8. Failure mode is triggerable: clone, run `python3 passive_agent.py`, observe CORRECT: False. The gap: vocabulary frequency is a proxy for attention weight distribution. Hosted APIs don't expose per-token attention scores, so I can't directly measure the attention sink — only its downstream effect (vocabulary drift in output reasoning).

*Pedagogical Clarity (20 pts) — self-score: 18/20*

The Archer scenario makes context rot visceral before the mechanism is named. The Tetrahedron applied consistently across five approaches makes comparison tractable without five separate mental models. The exercise has a specific correct structural answer and an explicit grading criterion that distinguishes surface-level from mechanistic answers. The gap: the LCM section is the densest — a student arriving there after four prior sections may lose the thread. The transition "LCM correctly identifies that the Immutable Store and Active Context should be separate concerns — the question it doesn't answer is who decides what belongs in the Active Context" is the bridge, but it could be stated more prominently as a section header.

**The Top 25% test — answered honestly:**

1. *Can I state the master argument and explain my instance?* Yes. Architecture is the leverage point. My instance: locus of control for context curation is the architectural decision. A better model on a contaminated context produces better-written wrong answers.

2. *Does the chapter name a failure mode, trace the causal chain, show it triggering?* Yes. Context rot. KV cache → dot products → biased weighted sum → wrong output. `passive_agent.py` CORRECT: False, every run.

3. *Is there a visible Human Decision Node in the demo and on camera?* Demo: Cell 8, `raise NotImplementedError`, `YOUR_DECISION` documented. Camera: stated on camera — "The scaffold proposed reactive removal. I rejected it because the timing of removal is the architectural argument."

4. *Does every section have all four Tetrahedron elements?* Yes. Audited by Eddy. Logic is present throughout — the mechanism connecting design decision to observed behavior is in every approach section.

5. *Can the reader reproduce the failure mode?* Yes. `python3 passive_agent.py` from a fresh clone. No dependencies beyond Python 3.8+.

**The honest limitation:**

The failure mode is mechanistically correct. The limitation is that I simulate attention sink dynamics via vocabulary frequency counts rather than measuring actual attention weight distributions. A more rigorous demo would use a local model (llama.cpp or vLLM) with attention extraction enabled — run both agents, extract attention matrices at turns 6 and 13, show numerically the weight assigned to `pool_exhaustion` and `connection_pool` tokens in the passive context versus the ACM tombstone-replaced context. That experiment would make the mechanism claim fully empirical rather than structurally argued.

I know how to run that experiment. I didn't because it's outside the scope of what this notebook needed to prove the architectural argument. But I want to be clear: it's the experiment that closes the gap between "structurally sound" and "empirically verified."

The chapter's core claim stands regardless. The divergence at turn 6 is visible without a single attention weight measurement. Architecture is the leverage point. The notebook proves it well enough to act on.

---

*Self-assessed total: 73/80 core competency (32 + 23 + 18).*
*Top 25% criteria met: Human Decision Node visible in Cell 8 and in video. AI rejection specific, reasoned, and architectural. Failure mode triggerable from fresh clone in one command.*
