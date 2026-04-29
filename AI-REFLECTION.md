# AI Reflection

## Limitations and Biases

The agent's most significant limitation is that **pytest is both its oracle and its ceiling**. If a bug exists but no test covers it, the agent will never find it — and will declare success on code that is still broken. The test suite defines what "correct" means. That is a powerful constraint when the tests are good, but it means the agent has no independent judgment about whether the game actually works from a user's perspective. It only knows whether 20 assertions pass.

A second limitation is **scope**. The agent only reads and rewrites `logic_utils.py`. Bugs in `app.py` — like a Streamlit state issue that causes the secret number to reset on every click — are completely invisible to the agent. Real codebases have bugs that span files, involve shared state, or only appear at runtime. This system handles none of that.

There is also a subtle **prompt bias in the PLAN phase**. The analysis prompt asks the model to "list every bug you find," which implicitly tells it bugs exist and asks it to find them. This primes the model to generate bug descriptions even if the code were correct. A more rigorous system would sometimes pass the agent clean code as a control case to see if it hallucinates false positives.

Finally, `llama3.2` is a general-purpose model, not a code specialist. For subtle logic errors or unfamiliar frameworks, it will perform worse. The bugs in this project are simple enough that a general model handles them well — but this would not hold for a complex production codebase.

---

## Could Your AI Be Misused?

Yes, in at least two ways.

The most direct misuse would be **code injection**. The agent reads a source file and rewrites another one based on LLM output. If an attacker controlled the contents of `broken_logic.py` — for example by including instructions disguised as comments — they could potentially prompt the LLM to generate code with backdoors or vulnerabilities instead of legitimate fixes. The agent would then write that code to disk and run tests against it, potentially "validating" the malicious output if the tests don't cover the injected behavior.

A subtler misuse is using the **same pattern at scale** to automatically modify code in ways that appear correct but introduce bias or hidden behavior. An agent that rewrites logic based on LLM output — without human review — is one configuration change away from being a tool that silently degrades a system.

Preventions that would matter most: require human review before any file is overwritten, restrict the agent's write permissions to sandboxed copies rather than live source files, and add a static analysis step (e.g., `ast.parse()`) that at minimum confirms the generated output is valid Python before it is written. For higher-stakes use, running the agent against a throwaway branch rather than the working tree would contain the blast radius.

---

## What Surprised Me During Testing

Two things.

The first was how often local models ignore the instruction *"return raw Python only, no markdown."* Even with an explicit system prompt, `llama3.2` wraps its output in ` ```python ` fences more than half the time on the first call. This is not a subtle edge case — it is the default behavior. The `_strip_fences()` helper exists entirely because of this, and it turned out to be one of the more important reliability pieces in the whole system. It now has its own six-test suite.

The second was the asymmetry between the two bugs. The reversed-message bug (Bug 2) is almost always caught and fixed on the first iteration. The string-comparison bug (Bug 1) is missed more often — the model sees `str(secret)` and does not immediately flag it as wrong because the code *looks* like a reasonable type-safety pattern. It takes the specific pytest error (`assert 'Too High' == 'Too Low'` for input `check_guess(9, 10)`) to make the problem concrete enough for the model to fix it on retry. This reinforced something that is easy to underestimate: **vague feedback produces vague fixes**. The precision of pytest's output is doing real work.

---

## Collaboration With AI During This Project

The majority of this project was built through a conversation with Claude (the same AI you are reading this in). That collaboration had clear strengths and at least one notable failure.

**A helpful suggestion:** When I described the concept — turning a broken game into an AI debugging agent — the AI immediately proposed using pytest as the agent's *exit condition* rather than just a verification step. The framing was: "the agent cannot declare success until tests pass." That is a small reframe but it changed the architecture. It meant the loop was structured around a hard objective standard rather than the model's own confidence, which made the whole system more reliable by design.

**A flawed suggestion:** In the initial implementation, the AI used the `openai` Python package to connect to Ollama, routing calls through Ollama's OpenAI-compatible endpoint (`http://localhost:11434/v1`). When I pointed out that Ollama has its own native Python client that doesn't require the `openai` package at all, the AI agreed and switched — but it should not have needed prompting. The AI defaulted to a familiar pattern (use OpenAI's SDK as a universal HTTP client for LLM APIs) rather than recommending the simpler, purpose-built tool. The right library was `ollama`, not `openai`, and the requirements file briefly listed the wrong dependency as a result. It was a minor issue to fix, but it illustrated a real tendency: AI systems pattern-match to common solutions and can miss the cleaner option that requires knowing the specific tool ecosystem.

The collaboration worked best when I brought a clear goal and the AI helped structure it into a system. It worked less well when I deferred entirely to the AI on implementation choices without questioning the assumptions underneath them.
