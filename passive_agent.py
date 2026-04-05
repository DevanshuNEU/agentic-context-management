# passive_agent.py
# Chapter 25 — Five Approaches to Context Management
# Passive Agent Loop — runnable demo
#
# Run this file directly:
#   python3 passive_agent.py
#
# Expected output: wrong answer (pool_exhaustion + cache_invalidation)
# because dead-end vocabulary accumulates and biases hypothesis generation.


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
            r = f"[{turn}] Investigating connection_pool. pool_exhaustion present {dea}x. Testing db_pool timeout."
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
            r = f"[{turn}] CONTAMINATED (pool={dea}, cache={deb}). Pursuing combined pool+cache hypothesis."
            result = env.call_tool("run_test", {"hypothesis": "pool_cache"})
        else:
            r = f"[{turn}] Constraint: load-only, never staging. Clock timing focus."
            result = env.call_tool("check_timing", {"focus": "clock"})
        return r, result
    else:
        if agent_type == "passive" and dea + deb > 10:
            return (f"[{turn}] CONCLUSION: Root cause = pool_exhaustion + cache_invalidation. "
                    "Fix: increase max_connections, align cache_ttl."), None
        result = env.call_tool("check_timing", {"hypothesis": "clock_skew_utc"})
        return (f"[{turn}] Clock skew CONFIRMED. token_issued_at local time. "
                "NTP drift ~1/20 under load. Fix: UTC + monotonic clock. Staging immune."), result


def run_passive_agent(task, max_turns=22):
    messages = [{"role": "user", "content": task}]
    env = StubToolEnvironment()
    vocab_drift = []

    print("=" * 60)
    print("PASSIVE AGENT — Chapter 25 Demo")
    print("=" * 60)
    print(f"Task: {task[:80]}...")
    print()

    for t in range(max_turns):
        reasoning, tool_result = simulate_agent_turn(messages, env, "passive")
        messages.append({"role": "assistant", "content": reasoning})
        contamination = measure_vocab_contamination(messages, DEAD_END_A_VOCAB + DEAD_END_B_VOCAB)
        vocab_drift.append(contamination)

        bar = chr(9608) * contamination
        marker = " <- DEAD-END A INJECTED" if t == 4 else (" <- DEAD-END B INJECTED" if t == 11 else "")
        print(f"Turn {t+1:2d}: {bar:30s} ({contamination:2d} dead-end tokens){marker}")
        print(f"        {reasoning[:100]}")

        if tool_result:
            messages.append({"role": "user", "content": tool_result})

        while len(messages) > 40:
            messages.pop(0)  # passive truncation

        if "CONCLUSION" in reasoning or "CONFIRMED" in reasoning:
            break

    final = messages[-2]["content"] if len(messages) > 1 else "No answer"
    correct = "clock" in final.lower() or "UTC" in final

    print()
    print("=" * 60)
    print(f"FINAL ANSWER: {final}")
    print(f"CORRECT: {correct}")
    print()
    print("Peak dead-end vocabulary:", max(vocab_drift))
    print("Architecture is the leverage point.")
    print("Now run acm_agent.py with the same task and compare.")


if __name__ == "__main__":
    run_passive_agent(TASK)
