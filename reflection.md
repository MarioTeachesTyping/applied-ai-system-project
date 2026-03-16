# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

When I first opened the game it appeared to work visually, but playing it revealed three serious bugs that made winning impossible.

Bug 1: New Game button locked the player out after winning.
The game would show a new secret number in the debug panel, but any subsequent guess was immediately blocked with "You already won. Start a new game to play again." The `new_game` block never reset `st.session_state.status` back to `"playing"`, so the won state was permanent.

Bug 2: On every other guess the game compared against the wrong type.   
On even-numbered attempts the code did `secret = str(st.session_state.secret)`, passing a string to `check_guess`. The function's `TypeError` fallback then did string-based comparisons (e.g. `"9" > "10"` is `True` in Python because `"9" > "1"`), producing completely wrong outcomes. The debug panel showed the correct integer, yet the comparison was secretly using the wrong type.

Bug 3: The Higher/Lower hints were backwards. 
The hint said "📈 Go HIGHER!" when my guess was above the secret, and "📉 Go LOWER!" when it was below, the exact opposite of what is helpful. This made it impossible to close in on the correct number by following the hints.

---

## 2. How did you use AI as a teammate?

I used GitHub Copilot's agent mode throughout this project.

Correct AI suggestion: Refactor all logic into `logic_utils.py` and fix the hint messages.  
I gave Copilot the prompt: *"Move the check_guess function to logic_utils.py, update the logic to fix the high/low bug, and update the import in app.py."* Copilot correctly identified that `if guess > secret` should return `"Too High"` with the message `"Go LOWER!"` (not "Go HIGHER!") and moved all four helper functions out of `app.py`. I verified the fix by running `pytest tests/ -v`, which confirmed `test_too_high_message_says_go_lower` and `test_too_low_message_says_go_higher` both passed, and by playing the live game where the hints now pointed me in the right direction.

Incorrect/misleading AI suggestion: Suggested fixing the string-comparison bug inside `check_guess` instead of removing the cast.  
Copilot's first response to Bug 2 suggested adding extra `isinstance` checks inside `check_guess` to handle both int and str secrets gracefully. That approach was misleading because it treated a symptom rather than the root cause: no version of `check_guess` should ever receive a string secret. The real fix was to delete the `if st.session_state.attempts % 2 == 0: secret = str(...)` block in `app.py` entirely. I verified the correct fix by writing `test_check_guess_integer_secret_no_string_fallback` — which would have passed even with the bandage fix — and then also checking the test `test_check_guess_high_integers` with a boundary value (101 vs 100) to confirm integer math was used throughout.

---

## 3. Debugging and testing your fixes

I decided a bug was truly fixed only when both a pytest case targeting that specific behaviour passed and the live Streamlit game behaved correctly for manual play.

For Bug 3 I wrote two tests: `test_too_high_message_says_go_lower` asserts that `check_guess(60, 50)` returns a message containing `"LOWER"`, and `test_too_low_message_says_go_higher` asserts that `check_guess(40, 50)` returns a message containing `"HIGHER"`. Before the fix both would have failed; after the fix both passed, giving me confidence the hints were corrected. Running `pytest tests/ -v` showed all 14 tests green (0 failures), confirming no regressions were introduced across all three bug fixes.

Copilot helped me design the test for Bug 2 (`test_check_guess_integer_secret_no_string_fallback`) by suggesting I use a near-boundary pair like `check_guess(99, 100)`, a case that string comparison would have gotten wrong (`"99" > "100"` is `True` in Python, but numerically 99 < 100). That test proved the integer path was being taken correctly.

---

## 4. What did you learn about Streamlit and state?

Streamlit reruns the entire Python script from top to bottom every time the user interacts with the app (clicks a button, changes a widget, etc.). Without `st.session_state`, any variable you set like the secret number or attempt count would be re-created from scratch on each rerun, making it impossible to track anything between clicks. `st.session_state` is a dictionary-like object that survives across reruns for the lifetime of the browser session, so values stored there (like `st.session_state.secret`) persist. The key lesson is that you must explicitly reset every piece of state you want cleared; Streamlit will never reset `session_state` for you unless you write code to do it. For a friend: think of Streamlit as a photocopier that reprints the whole page every time you press a button, `session_state` is a sticky-note you tape to the machine that survives each reprint.

---

## 5. Looking ahead: your developer habits

Habit I want to reuse: Writing a failing test *before* fixing a bug ("test-first debugging"). For each bug I first confirmed what the wrong behavior looked like in a test assertion, then changed the code until the test passed. That order gave me a clear, repeatable definition of "fixed."

What I'd do differently: Next time I use AI in Agent mode I'll read every diff line before accepting it. Copilot's first suggestion for Bug 2 added complexity inside `check_guess` instead of removing the bad code in `app.py`; accepting it blindly would have hidden the real bug. A targeted prompt like *"remove the string cast in app.py rather than patching check_guess"* would have saved me from reviewing a misleading change.

How this project changed how I think about AI-generated code: AI can produce code that looks completely plausible and passes a surface-level review while hiding subtle type-mismatch bugs (like the string-vs-int comparison) that only surface under specific runtime conditions. I now treat AI-generated code the way I'd treat code from a junior developer: useful as a starting point, but every logical branch needs to be read critically and backed by a test before it's trusted.

