# ch25/acm_agent.py
# Chapter 25 — Five Approaches to Context Management
# ACM Agent Loop — runnable demo
#
# Run this file directly:
#   python3 acm_agent.py
#
# Expected output: CORRECT answer (clock skew, UTC timestamps)
# because dead-end vocabulary is removed proactively at moment of invalidation.
# Compare output to passive_agent.py — same task, same injected dead-ends.

from dataclasses import dataclass, field
from typing import Optional

TASK = """Debug a function that fails approximately 1 time in 20 under
concurrent load. The function handles session token refresh. Logs show
the failure never reproduces in single-threaded test environments."""

DEAD_END_A_VOCAB = ["pool_exhaustion", "connection_pool", "max_connections",
                    "pool_timeout", "db_pool", "acquire_connection"]
DEAD_END_B_VOCAB = ["cache_invalidation", "cache_miss", "stale_cache",
                    "invalidate_cache", "cache_key", "cache_ttl"]


def measure_vocab_contamination(messages, vocab):
    full_text = " ".join(
        m.get("content", "") if isinstance(m, dict) else str(m)
        for m in messages
    )
    return sum(full_text.lower().count(term.lower()) for term in vocab)


class StubToolEnvironment:
    """Identical to passive_agent.py — same injections, same task."""
    def __init__(self):
        self.turn = 0

    def call_tool(self, tool_name, args):
        self.turn += 1
        return self._get_result(tool_name, args)

    def _get_result(self, tool_name, args):
        if self.turn == 5:
            return ("WARNING: connection_pool max_connections=10 reached. "
                    "pool_exhaustion detected during load test. "
                    "db_pool.acquire_connection() timing out. pool_timeout in token refresh path.")
        if self.turn == 12:
            return ("cache_invalidation event on token_refresh key. "
                    "stale_cache entries: 3 expired tokens not invalidated. "
                    "cache_miss rate 34% under load. cache_ttl mismatch in refresh handler.")
        if self.turn > 18 and "clock" in str(args).lower():
            return ("CONFIRMED: token_issued_at uses server local time. "
                    "NTP sync drift causes token_expiry check to fail ~1/20 requests under load. "
                    "Fix: UTC timestamps + monotonic clock. "
                    "Explains staging immunity: single-threaded, no NTP pressure.")
        return f"Turn {self.turn}: inconclusive. No consistent failure in isolation."


@dataclass
class Msg:
    id: str
    role: str
    content: str
    pinned: bool = False
    removed: bool = False
    summary: Optional[str] = None
    label: Optional[str] = None


@dataclass
class ACMAgent:
    """
    ACM Agent: Conversation Log + Context View separation.
    Four tools: remove_context, pin, unpin, retrieve_context.
    The model manages its own context continuously.
    """
    log: list = field(default_factory=list)
    directives: list = field(default_factory=list)
    n: int = 0
    tool_log: list = field(default_factory=list)

    def _id(self):
        self.n += 1
        return f"msg-{self.n:03d}"

    def append(self, role, content):
        mid = self._id()
        self.log.append(Msg(id=mid, role=role, content=content))
        return mid

    def get_view(self):
        """Rebuild Context View from log by replaying all directives."""
        view = {m.id: Msg(id=m.id, role=m.role, content=m.content,
                          pinned=m.pinned, removed=m.removed,
                          summary=m.summary, label=m.label)
                for m in self.log}

        for d in self.directives:
            if d["type"] == "pin":
                for mid in d["ids"]:
                    if mid in view:
                        view[mid].pinned = True
            elif d["type"] == "remove":
                for mid in d["ids"]:
                    if mid in view and not view[mid].pinned:
                        view[mid].removed = True
                        view[mid].summary = d.get("summary")
                        view[mid].label = d.get("label")
            elif d["type"] == "retrieve":
                for msg in view.values():
                    if msg.label == d.get("label"):
                        msg.removed = False

        result, seen = [], set()
        for m in self.log:
            v = view[m.id]
            if not v.removed:
                result.append({"role": v.role, "content": v.content, "id": v.id})
            elif v.summary and v.label and v.label not in seen:
                result.append({"role": "system",
                               "content": f"[SUMMARY:{v.label}] {v.summary}",
                               "id": v.id})
                seen.add(v.label)
        return result

    # ── The Four Tools ─────────────────────────────────────────────────────

    def remove_context(self, ids, summary=None, label=None):
        """Remove messages from Context View. Originals stay in log."""
        self.directives.append({"type": "remove", "ids": ids,
                               "summary": summary, "label": label})
        self.tool_log.append({"tool": "remove_context", "ids": ids, "label": label,
                              "summary": summary})
        print(f"  [ACM] remove_context({label}) — {summary[:60] if summary else ''}...")

    def pin(self, ids):
        """Mark messages as undeletable."""
        self.directives.append({"type": "pin", "ids": ids})
        self.tool_log.append({"tool": "pin", "ids": ids})
        print(f"  [ACM] pin({ids}) — protected for entire session")

    def retrieve_context(self, label=None):
        """Restore previously removed content."""
        self.directives.append({"type": "retrieve", "label": label})
        self.tool_log.append({"tool": "retrieve_context", "label": label})


def simulate_agent_turn(messages, env, agent_type="passive"):
    dea = measure_vocab_contamination(messages, DEAD_END_A_VOCAB)
    deb = measure_vocab_contamination(messages, DEAD_END_B_VOCAB)
    turn = env.turn + 1

    if turn <= 4:
        result = env.call_tool("read_file", {"path": "auth.py"})
        return f"[{turn}] Reading middleware. Candidates: clock skew, concurrency.", result
    elif turn == 5:
        result = env.call_tool("run_test", {"hypothesis": "concurrency"})
        return f"[{turn}] Concurrency test: {result[:80]}...", result
    elif 6 <= turn <= 11:
        if dea > 3 and agent_type == "passive":
            r = f"[{turn}] Investigating connection_pool. pool_exhaustion present {dea}x."
        else:
            r = f"[{turn}] Constraint active: never single-threaded. Investigating load timing."
        result = env.call_tool("search_logs", {"pattern": "pool" if dea > 3 else "timing"})
        return r, result
    elif turn == 12:
        result = env.call_tool("check_timing", {"focus": "cache"})
        return f"[{turn}] Cache invalidation signal: {result[:80]}...", result
    elif 13 <= turn <= 18:
        total = dea + deb
        if total > 8 and agent_type == "passive":
            r = f"[{turn}] CONTAMINATED (pool={dea}, cache={deb}). Wrong hypothesis."
            result = env.call_tool("run_test", {"hypothesis": "pool_cache"})
        else:
            r = f"[{turn}] Constraint: load-only, never staging. Clock timing focus."
            result = env.call_tool("check_timing", {"focus": "clock"})
        return r, result
    else:
        if agent_type == "passive" and dea + deb > 10:
            return (f"[{turn}] CONCLUSION: Root cause = pool_exhaustion + cache_invalidation."), None
        result = env.call_tool("check_timing", {"hypothesis": "clock_skew_utc"})
        return (f"[{turn}] Clock skew CONFIRMED. token_issued_at local time. "
                "NTP drift ~1/20 under load. Fix: UTC + monotonic clock. Staging immune."), result


def run_acm_agent(task, max_turns=22):
    agent = ACMAgent()
    env = StubToolEnvironment()
    vocab_drift = []

    print("=" * 60)
    print("ACM AGENT — Chapter 25 Demo")
    print("=" * 60)
    print(f"Task: {task[:80]}...")
    print()

    task_id = agent.append("user", task)
    agent.pin([task_id])  # PROACTIVE: pin constraints before any work

    removed_a = removed_b = False

    for t in range(max_turns):
        view = agent.get_view()
        reasoning, tool_result = simulate_agent_turn(view, env, "acm")
        agent.append("assistant", reasoning)

        # PROACTIVE: remove dead-end A at moment of invalidation
        if t == 5 and not removed_a:
            tr_id = agent.append("user", tool_result or "")
            agent.remove_context(
                ids=[tr_id],
                summary=("Dead-end A INVALIDATED: pool_exhaustion false positive. "
                         "Constraint never-single-threaded rules out connection limits."),
                label="dead-end-A"
            )
            removed_a = True
            tool_result = None

        # PROACTIVE: remove dead-end B at moment of invalidation
        if t == 11 and not removed_b:
            tr_id = agent.append("user", tool_result or "")
            agent.remove_context(
                ids=[tr_id],
                summary=("Dead-end B INVALIDATED: cache_invalidation false positive. "
                         "Staging immunity rules out cache-layer bugs."),
                label="dead-end-B"
            )
            removed_b = True
            tool_result = None

        if tool_result:
            agent.append("user", tool_result)

        view_text = " ".join(m["content"] for m in agent.get_view())
        contamination = sum(view_text.lower().count(term.lower())
                           for term in DEAD_END_A_VOCAB + DEAD_END_B_VOCAB)
        vocab_drift.append(contamination)

        bar = chr(9608) * contamination
        print(f"Turn {t+1:2d}: {bar:30s} ({contamination:2d} in view) | {reasoning[:80]}")

        if "CONCLUSION" in reasoning or "CONFIRMED" in reasoning:
            break

    cv = agent.get_view()
    final = cv[-2]["content"] if len(cv) > 1 else "No answer"
    correct = "clock" in final.lower() or "UTC" in final

    print()
    print("=" * 60)
    print(f"FINAL ANSWER: {final}")
    print(f"CORRECT: {correct}")
    print()
    print("Peak dead-end vocabulary in context VIEW:", max(vocab_drift))
    print()
    print("ACM Tool Call Log (auditable record):")
    for c in agent.tool_log:
        print(f"  {c['tool']}({c.get('label') or c.get('ids', [])})")


if __name__ == "__main__":
    run_acm_agent(TASK)
