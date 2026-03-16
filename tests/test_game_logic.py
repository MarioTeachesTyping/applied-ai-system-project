from logic_utils import check_guess, parse_guess, get_range_for_difficulty

# --- Existing starter tests (updated to unpack the (outcome, message) tuple) ---

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"


# --- Bug 3 fix: hint messages must point in the correct direction ---

def test_too_high_message_says_go_lower():
    # Bug 3: original message said "Go HIGHER!" when guess was too high (backwards).
    # Fixed: a guess above the secret should tell the player to go LOWER.
    _, message = check_guess(60, 50)
    assert "LOWER" in message

def test_too_low_message_says_go_higher():
    # Bug 3: original message said "Go LOWER!" when guess was too low (backwards).
    # Fixed: a guess below the secret should tell the player to go HIGHER.
    _, message = check_guess(40, 50)
    assert "HIGHER" in message


# --- Bug 2 fix: check_guess must always work with integer secrets ---

def test_check_guess_integer_secret_no_string_fallback():
    # Bug 2: on even attempts the secret was cast to str, causing broken comparisons.
    # Fixed: check_guess now only receives integers and never needs the TypeError branch.
    outcome, _ = check_guess(99, 100)
    assert outcome == "Too Low"

def test_check_guess_high_integers():
    outcome, _ = check_guess(101, 100)
    assert outcome == "Too High"


# --- parse_guess edge cases ---

def test_parse_guess_valid_integer():
    ok, value, err = parse_guess("42")
    assert ok is True
    assert value == 42
    assert err is None

def test_parse_guess_empty_string():
    ok, value, err = parse_guess("")
    assert ok is False
    assert value is None

def test_parse_guess_non_numeric():
    ok, value, err = parse_guess("abc")
    assert ok is False

def test_parse_guess_float_rounds_down():
    ok, value, err = parse_guess("7.9")
    assert ok is True
    assert value == 7


# --- get_range_for_difficulty ---

def test_range_easy():
    assert get_range_for_difficulty("Easy") == (1, 20)

def test_range_normal():
    assert get_range_for_difficulty("Normal") == (1, 100)

def test_range_hard():
    assert get_range_for_difficulty("Hard") == (1, 50)
