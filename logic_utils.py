def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    elif difficulty == "Normal":
        return 1, 100
    elif difficulty == "Hard":
        return 1, 50
    else:
        raise ValueError("Invalid difficulty level")


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        value = int(raw)
    except ValueError:
        return False, None, "That is not an integer."
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    """
    Compare guess to secret and return (outcome, message).
    """
    if guess > secret:
        # Corrected hint message
        return "Too High", "📈 Go LOWER!"
    elif guess < secret:
        # Corrected hint message
        return "Too Low", "📉 Go HIGHER!"
    else:  # Corrected logic for correct guess
        return "Win", "🎉 Correct!"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - (10 * (attempt_number + 1))
        return current_score + min(points, 10)

    # Corrected scoring for too high or low attempts
    return current_score


def play_game():
    difficulty = input("Choose a difficulty level: ")
    try:
        lower, upper = get_range_for_difficulty(difficulty)
        secret = lower + (upper - lower) * random.randint(0, 1)
    except ValueError as e:
        print(e)
        return

    while True:
        guess = int(input("Guess the number between {} and {}: ".format(lower, upper)))
        if guess < lower or guess > upper:
            print("Please enter a number within the range.")
            continue
        if not parse_guess(guess):
            print("Invalid input. Please try again.")
            continue

        outcome = check_guess(guess, secret)
        message, _ = outcome

        current_score = update_score(0, *outcome)

        if guess == secret:
            print(message)
            break
        else:
            print(message)


import random


if __name__ == "__main__":
    play_game()