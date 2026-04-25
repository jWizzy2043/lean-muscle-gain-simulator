
import os
import json
from datetime import datetime


# The JSON file where all workout and bodyweight data is stored
LOG_FILE = "fitness_log.json"


# ─────────────────────────────────────────────
#  here, we want to add a feature that will be able to log the data for us. this is especially desirable for a fitness tracker python project! here, the main idea is that these will be the fuinctinosd that are touching the disk and all the other functions will only work within in memory dictionaries known as save_log
# ─────────────────────────────────────────────

def load_log():
    """Load existing log from disk, or return a fresh empty log."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    # Default structure if no log file exists yet
    return {"workouts": [], "bodyweight": []}


def save_log(log):
    """Persist the in-memory log dict to disk as formatted JSON."""
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


# ─────────────────────────────────────────────
#  Feature: here, we need bodyweight to be logged.
# ─────────────────────────────────────────────

def log_bodyweight(log):
    """Prompt the user for their bodyweight and save it with today's date."""
    date = datetime.today().strftime("%Y-%m-%d")

    while True:
        try:
            weight = float(input("Enter bodyweight (lbs): "))
            break
        except ValueError:
            print("  Please enter a valid number (e.g. 185.5).\n")

    log["bodyweight"].append({"date": date, "weight": weight})
    save_log(log)
    print(f"  ✓ Logged {weight} lbs on {date}.\n")


# ─────────────────────────────────────────────
#  Feature: here, we need the particular workout session to be logged as well
# ─────────────────────────────────────────────

def log_workout(log):
    """
    Record a full workout session. The user enters as many exercises
    as they want, with sets × reps × weight for each. Entering a blank
    exercise name ends the session.
    """
    date = datetime.today().strftime("%Y-%m-%d")
    session_name = input("Workout name (e.g. 'Push Day', 'Full Body'): ").strip()
    exercises = []

    print("  Enter exercises below. Leave the exercise name blank when done.\n")

    while True:
        exercise_name = input("  Exercise name (or press Enter to finish): ").strip()
        if not exercise_name:
            break

        sets = []
        while True:
            try:
                num_sets = int(input(f"    How many sets for {exercise_name}? "))
                break
            except ValueError:
                print("    Please enter a whole number.\n")

        for i in range(1, num_sets + 1):
            while True:
                try:
                    reps   = int(input(f"    Set {i} — Reps: "))
                    weight = float(input(f"    Set {i} — Weight (lbs, enter 0 for bodyweight): "))
                    break
                except ValueError:
                    print("    Please enter valid numbers.\n")

            sets.append({"set": i, "reps": reps, "weight": weight})

        exercises.append({"exercise": exercise_name, "sets": sets})
        print()

    if not exercises:
        print("  No exercises recorded. Workout not saved.\n")
        return

    # we need to append the session object just in case
    session = {
        "date": date,
        "name": session_name,
        "exercises": exercises
    }
    log["workouts"].append(session)
    save_log(log)
    print(f"  ✓ Workout '{session_name}' saved ({len(exercises)} exercise(s)).\n")


# ─────────────────────────────────────────────
#  here, it may be useful to have different types of body statistics stored in order for summaries to be used
# ─────────────────────────────────────────────

def show_bodyweight_stats(log):
    """Display a history of all bodyweight entries and the net change."""
    entries = log["bodyweight"]

    if not entries:
        print("  No bodyweight data logged yet.\n")
        return

    print("\n  ── Bodyweight History ──────────────────────")
    for entry in entries:
        print(f"  {entry['date']}   {entry['weight']} lbs")

    # Show net change between first and most recent weigh-in
    if len(entries) > 1:
        first  = entries[0]["weight"]
        latest = entries[-1]["weight"]
        change = round(latest - first, 1)
        direction = "+" if change >= 0 else ""
        print(f"\n  Net change: {direction}{change} lbs  ({entries[0]['date']} → {entries[-1]['date']})")

    print()


def show_workout_history(log):
    """Print a summary of every logged workout session."""
    workouts = log["workouts"]

    if not workouts:
        print("  No workouts logged yet.\n")
        return

    print("\n  ── Workout History ─────────────────────────")
    for session in workouts:
        print(f"\n  [{session['date']}] {session['name']}")
        for ex in session["exercises"]:
            # Summarise each exercise on one line: name → sets × reps @ weight
            set_summary = ",  ".join(
                f"Set {s['set']}: {s['reps']} reps @ {s['weight']} lbs"
                for s in ex["sets"]
            )
            print(f"    {ex['exercise']}: {set_summary}")
    print()


def show_exercise_pr(log):
    """
    For a given exercise, find the heaviest single set ever logged
    (i.e. the all-time personal record for that movement).
    """
    workouts = log["workouts"]

    if not workouts:
        print("  No workouts logged yet.\n")
        return

    exercise_name = input("  Enter exercise name to look up PR: ").strip().lower()

    best_weight = None
    best_date   = None

    for session in workouts:
        for ex in session["exercises"]:
            # Case-insensitive match so "Bench Press" == "bench press"
            if ex["exercise"].lower() == exercise_name:
                for s in ex["sets"]:
                    if best_weight is None or s["weight"] > best_weight:
                        best_weight = s["weight"]
                        best_date   = session["date"]

    if best_weight is None:
        print(f"  No data found for '{exercise_name}'.\n")
    else:
        print(f"\n  PR for '{exercise_name}': {best_weight} lbs  (logged on {best_date})\n")


def show_stats_menu(log):
    """Sub-menu for the progress & stats section."""
    options = {
        "1": ("Bodyweight history",   lambda: show_bodyweight_stats(log)),
        "2": ("Full workout history", lambda: show_workout_history(log)),
        "3": ("Personal record (PR) for an exercise", lambda: show_exercise_pr(log)),
    }

    while True:
        print("  Stats & Progress")
        print("  ────────────────")
        for key, (label, _) in options.items():
            print(f"  {key}. {label}")
        print("  0. Back\n")

        choice = input("  Choose: ").strip()

        if choice == "0":
            break
        elif choice in options:
            print()
            options[choice][1]()   # call the matching function
        else:
            print("  Invalid choice.\n")


# ─────────────────────────────────────────────
# this is just the general "menu," if you will, for the fitness tracker purposes
# ─────────────────────────────────────────────

def main():
    log = load_log()

    menu = {
        "1": ("Log bodyweight",       lambda: log_bodyweight(log)),
        "2": ("Log a workout",        lambda: log_workout(log)),
        "3": ("Stats & progress",     lambda: show_stats_menu(log)),
    }

    print("\n══════════════════════════════")
    print("   Fitness Tracker CLI")
    print("══════════════════════════════\n")

    while True:
        print("  Main Menu")
        print("  ─────────")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")
        print("  0. Quit\n")

        choice = input("  Choose: ").strip()

        if choice == "0":
            print("  Goodbye!\n")
            break
        elif choice in menu:
            print()
            menu[choice][1]()   # call the matching function
        else:
            print("  Invalid choice — try again.\n")


if __name__ == "__main__":
    main()
