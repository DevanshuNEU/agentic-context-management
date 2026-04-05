# Author's Note — Chapter 25: Five Approaches to Context Management

*Devanshu Chicholikar | MS Software Engineering Systems, Northeastern University*

---

## Page 1 — Design Choices

I picked context management because I've been burned by it.

Not in a dramatic way. In the way where you run an agent for 20 minutes, get back a confident answer, ship the fix, and then spend another hour figuring out why it didn't work. The agent wasn't wrong in any obvious sense. Its reasoning was coherent. Its output was well-formatted. It just happened to be answering a slightly different question than the one you asked — one shaped by dead-end vocabulary from 45 minutes ago that never left its context.

That's the failure this chapter is about. And the reason I spent time on it is that most engineers I've seen encounter this misattribute it. They think the model hallucinated. They think the prompt was bad. They scale up to a better model. None of those fix it, because none of those touch the actual problem: the architecture of who controls context curation.

**The book's master argument is that architecture is the leverage point, not the model.** My chapter is a specific instance of that claim: the locus of control for context curation is an architectural decision, and it determines the failure mode. A better model attending to a contaminated context produces better-written wrong answers. The intervention has to be at the architectural layer.

I anchored everything to Archer — a single agent, a single task, a single 5-hour session — because abstract systems explanations fail when they don't make the failure visceral. The 9:47 AM start time, the 3:00 PM wrong patch, the specific token counts (11x `lock_acquired_at`, 19x `timestamp`) — those specifics are doing real work. They're not decoration. They let a reader feel the drift before they understand the mechanism.

**What I left out deliberately:**

Hybrid approaches — ACM layered on top of LCM — are real and probably more robust than either alone. I excluded them because the chapter's job is to make the design decision legible, not to present the optimal production setup. Once you understand why ACM and LCM make different bets, you can compose them. Teaching the composition before the bets are clear would produce confusion, not understanding.

Fine-tuning for metacognitive accuracy is the obvious next question after ACM. If the model's judgment about its own context is the leverage point, then improving that judgment through fine-tuning should matter. I excluded it because that's a training-time intervention and this chapter is about inference-time architecture. They're different levers.

The interaction between context management strategy and model capability is real — smaller models may need more aggressive proactive removal because their metacognitive accuracy is lower. I excluded it because quantifying that interaction requires empirical data I don't have, and I'd rather be honest about the gap than speculate.

---

## Page 2 — Tool Usage

**Bookie — what it got right and where I corrected it**

Bookie generated strong prose throughout. The Archer scenario came back nearly publication-ready on the first pass. The Tetrahedron structure (Structure / Logic / Implementation / Outcome) applied consistently across all five approaches is Bookie's work — I directed it, but it executed the parallel structure better than I would have drafting from scratch.

The corrections I made matter more than the generation:

*Correction 1 — KV cache mechanism framing.* Bookie's first draft of the Scenario Tetrahedron Read wrote: *"attention mechanisms weight tokens partly by position and partly by learned relevance patterns."* That's not wrong but it's too vague to be useful. The real mechanism is attention sink behavior driven by KV cache persistence — dead-end tokens remain in the KV cache and are attended to on every forward pass, and the softmax normalization means high-salience tokens win attention budget at the expense of everything else. I corrected this and moved the mechanistic language out of the Scenario section entirely, replacing it with a forward reference. The mechanism section now earns the claims the Scenario section makes.

*Correction 2 — RLM benchmark claim.* Bookie cited RLM's performance as "two orders of magnitude beyond model context windows" without sourcing the claim. I traced it to secondary analysis (Dead Neurons Substack) rather than the Zhang, Kraska, Khattab paper directly. I kept the claim but scoped it as secondary-sourced. This matters because the chapter explicitly criticizes benchmark selection bias in the RLM section — I can't make that argument while uncritically accepting an unsourced benchmark figure.

*Correction 3 — ACM promissory note.* Bookie wrote: *"This is the dimension on which ACM will improve as models improve."* That's a forward-looking claim with no grounding. I replaced it with: the honest answer is that metacognitive error rates in ACM-style deployments aren't well-measured in published literature yet, and an engineering team adopting ACM should instrument the error rate from first deployment rather than assuming it's low. The comparison between ACM and passive approaches is currently between a known error rate and an unknown one — and that asymmetry is itself part of the architectural argument, not evidence that ACM is error-free.

**Eddy the Editor — what I accepted and what I pushed back on**

Eddy flagged 13 issues. I accepted 5, rejected 3 with reasoning, and noted the rest in passing.

*Accepted:* KV cache language before mechanism existed (resolved by forward reference), softmax undefined in the mechanism section (added one sentence: softmax converts raw scores to weights that sum to 1.0, so stronger scores win a larger share of a fixed attention budget — this is what makes attention sink behavior concentrating rather than merely additive), DAG undefined on first use (added parenthetical on first mention), ACM metacognitive error rate ungrounded (corrected as above), and the position-based selection criterion in compaction not traced to the design decision it represents (added: changing the criterion to "least semantically relevant" would require calling the model, which changes the architecture from engine-driven to model-participatory — that's not a tweak, it's a different approach).

*Rejected — Failure 11 (LCM strengths front-loaded):* Eddy wanted me to reorder strengths → infrastructure cost → failure mode. I kept strengths → failure mode → infrastructure cost because it mirrors how a practitioner evaluates a system. You credit it before you critique it. Burying the strengths after the cost creates a false impression that LCM is a bad system. It isn't. It's a well-engineered system with the wrong problem.

*Rejected — Failure 12 (benchmark selection meta-critique):* Eddy wanted a sentence explaining that RLM's benchmarks were chosen to demonstrate the architecture's strengths. I added the sentence about benchmarks being chosen to demonstrate fit-for-purpose rather than general superiority, but I didn't add the full meta-critique about how this is "standard practice in architecture papers." That would make the RLM section about AI evaluation methodology rather than context management architecture.

*Rejected — Failure 6 (KV entry conflation in Approach 1 Logic):* Eddy wanted me to replace "the attention computation weighted both sets of KV entries" with "the query vectors at the current position produced high dot-product scores against both sets of key vectors, pulling the weighted sum of value vectors toward both framings simultaneously." I accepted this one — it's more precise and consistent with the mechanism section.

---

## Page 3 — Self-Assessment

**Against the rubric:**

*Architectural Rigor (35 pts):* The chapter correctly identifies the failure mode (context rot via attention sink behavior), traces the causal chain (stale KV cache entries → high dot-product scores → biased value-weighted sum → wrong output), and demonstrates the failure triggered and observed in the notebook. The five-approach comparison is honest — I credit LCM's genuine strengths before naming its limitation, and I acknowledge ACM's failure mode clearly rather than presenting it as a solution that always works. I'd give myself 31/35. The gap: I don't have empirical data on metacognitive error rates in production ACM deployments, which means the comparison between ACM and passive approaches is partly structural argument rather than measured evidence.

*Technical Implementation (25 pts):* The notebook runs end-to-end, the Human Decision Node requires a decision before proceeding, and the failure mode is triggerable by anyone who clones the repo and runs the passive agent with the injected dead-ends. The comparison output shows vocabulary drift per turn with the divergence point visible at turn 6. I'd give myself 22/25. The gap: the vocabulary frequency metric is a proxy for attention weight distribution, not a direct measurement. Hosted APIs don't expose per-token attention scores.

*Pedagogical Clarity (20 pts):* The Archer scenario makes context rot visceral before the mechanism is named. The Tetrahedron applied consistently across five approaches makes comparison tractable without requiring five separate mental models. The exercise has a specific correct structural answer and an explicit grading criterion that distinguishes surface-level answers from mechanistic ones. I'd give myself 18/20. The gap: the LCM section is the longest and densest — a student hitting it after four prior approaches may lose the thread. A cleaner transition from LCM to ACM would help.

**The honest limitation:**

The failure mode in this chapter is mechanistically correct. Context rot via attention sink behavior is real, and the notebook demonstrates it via vocabulary frequency as a proxy for attention weight. The limitation is that I simulate attention sink dynamics by counting vocabulary occurrences rather than measuring actual attention weight distributions, because hosted inference APIs don't expose per-token attention scores.

A more rigorous demo would use a local model — llama.cpp or vLLM — with attention extraction enabled. You'd run the passive and ACM agents on the same task, extract the attention matrices at turns 6 and 13, and show numerically how much weight is assigned to `pool_exhaustion` and `connection_pool` tokens in the passive agent's context versus the ACM agent's tombstone-replaced context. That experiment would make the mechanism claim fully empirical rather than structurally argued.

I know how to run that experiment. I didn't run it because it's outside the scope of what this notebook needed to prove the architectural argument. But I want to be clear that it's the experiment that would close the gap between "structurally sound" and "empirically verified."

The chapter's core claim stands regardless: the locus of control for context curation determines the failure mode. You can verify that claim by reading the passive agent's session log and the ACM agent's session log side by side. The divergence at turn 6 is visible without a single attention weight measurement.

Architecture is the leverage point. The notebook proves it well enough to act on.

---

*Total self-assessed score: 71/80 core competency. Top 25% criteria: Human Decision Node is visible in Cell 8 of the notebook and documented in Page 2 of this note. AI rejection is specific, reasoned, and architectural — not just preference.*
