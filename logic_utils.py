def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    elif difficulty == "Normal":
        return 1, 100
    elif difficulty == "Hard":
        return 1, 50


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    try:
        value = int(raw)
    except ValueError:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", f"Correct! You guessed the number in {1} attempt(s)."
    elif guess > secret:
        return "Too High", "Go LOWER!"
    else:
        return "Too Low", "Go HIGHER!"


def update_score(current_score: int, outcome: str):
    """Update score based on outcome."""
    if outcome == "Win":
        # Calculate points correctly
        points = 100 - (current_score // 10) * 10
        return current_score + points
    elif outcome in ["Too High", "Too Low"]:
        # Deduct consistent points for incorrect guesses
        return current_score - 5
    else:
        # Handle unexpected outcomes
        return current_score


def game():
    print("Welcome to the number guessing game!")
    difficulty = input("Choose a difficulty (Easy/Normal/Hard): ")
    min_val, max_val = get_range_for_difficulty(difficulty)
    
    attempts = 0
    while True:
        guess = parse_guess(input(f"Guess a number between {min_val} and {max_val}: "))
        
        if not guess[0]:
            print(guess[2])
            continue
        
        secret = random.randint(min_val, max_val)
        
        outcome = check_guess(guess[1], secret)
        score = update_score(0, outcome)
        
        attempts += 1
        print(outcome)
        print(f"Your current score is: {score}")
        
        if outcome == "Win":
            break


import random

game()