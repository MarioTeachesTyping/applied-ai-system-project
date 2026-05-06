def get_range_for_difficulty(difficulty):
    if difficulty == 'Easy': return 1, 20
    if difficulty == 'Normal': return 1, 100
    if difficulty == 'Hard': return 1, 50
    return 1, 100

def parse_guess(raw):
    if not raw: return False, None, 'Enter a guess.'
    try:
        v = int(float(raw)) if '.' in raw else int(raw)
    except Exception:
        return False, None, 'That is not a number.'
    return True, v, None

def check_guess(guess, secret):
    if guess == secret: return 'Win', 'Correct!'
    if guess > secret: return 'Too High', 'Go LOWER!'
    return 'Too Low', 'Go HIGHER!'

def update_score(current_score, outcome, attempt_number):
    if outcome == 'Win':
        return current_score + max(10, 100 - 10 * (attempt_number + 1))
    if outcome in ('Too High', 'Too Low'): return current_score - 5
    return current_score
