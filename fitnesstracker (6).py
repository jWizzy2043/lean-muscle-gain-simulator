"""
fitness_tracker.py  ─  CS32 Final Project
Author: J
Description:
    A command-line fitness tracker that lets users:
       Log daily bodyweight readings
       Log full workout sessions (exercise → sets → reps × weight)
    Search existing exercises from a built-in catalog + past workouts
      View personal records (PRs) for any exercise
    Plot bodyweight trends and workout-volume charts using matplotlib
    All data persists between runs in a local JSON file (fitness_log.json).
"""

import os
import json
from datetime import datetime

# matplotlib is used to generate charts which is a new concept that iz particularly useful here.
# import early on is important to prevent package delays

try:
    import matplotlib
    matplotlib.use("Agg")           # non-interactive backend (works anywhere)
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("  [Note] matplotlib not installed — chart features disabled.")
    print("         Run:  pip install matplotlib\n")





LOG_FILE = "fitness_log.json"

# Hard-coded exercise catalog grouped by muscle focus.
# When a user logs a new exercise, we show this list so they can pick one
# instead of typing a name from scratch (avoids case/typo sensitivity).
EXERCISE_CATALOG = {
    "Push (Chest / Shoulders / Triceps)": [
        "Bench Press", "Incline Bench Press", "Dumbbell Fly",
        "Overhead Press", "Lateral Raise", "Tricep Pushdown",
        "Skull Crusher", "Dips", "Push-Up",
    ],
    "Pull (Back / Biceps)": [
        "Pull-Up", "Lat Pulldown", "Seated Cable Row",
        "Barbell Row", "Dumbbell Row", "Face Pull",
        "Bicep Curl", "Hammer Curl", "Chin-Up",
    ],
    "Legs": [
        "Squat", "Romanian Deadlift", "Leg Press",
        "Leg Extension", "Leg Curl", "Hip Thrust",
        "Calf Raise", "Lunge", "Bulgarian Split Squat",
    ],
    "Core / Full Body": [
        "Deadlift", "Plank", "Ab Wheel Rollout",
        "Hanging Leg Raise", "Cable Crunch", "Farmer's Carry",
    ],
}


## we only needs these two functs to ever touch the json files






def load_log() -> dict:
    """Load the fitness log from disk, or return a blank log if none exists."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    # Default structure when starting fresh
    return {"workouts": [], "bodyweight": []}


def save_log(log: dict) -> None:
    """Write the in-memory log dictionary back to disk as formatted JSON."""
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


##4need an exercise search helper




_master_exercise_list(log: dict) -> list[str]:
    """
    Return a deddef builduplicated list of every known exercise name:
    catalog entries + any custom exercises already logged by the user.
    """
    master = []
    # Add every exercise from the built-in catalog
    for exercises in EXERCISE_CATALOG.values():
        master.extend(exercises)
    # Add custom exercises from past workout logs (user may have added their own)
    for session in log["workouts"]:
        for ex in session["exercises"]:
            name = ex["exercise"]
            if name not in master:
                master.append(name)
    return master


def search_exercise(log: dict, prompt: str = "Search exercise") -> str:
    """
    Interactive fuzzy search: user types a substring and sees matching
    exercises from the combined catalog + past workouts.  Returns the chosen
    exercise name.  Typing nothing and pressing Enter allows a custom entry.
    """
    master = build_master_exercise_list(log)

    while True:
        query = input(f"\n  {prompt} (type to search, or press Enter to type custom): ").strip()

        if not query:
            # Let the user type a completely custom name
            custom = input("  Enter custom exercise name: ").strip()
            if custom:
                return custom
            print("  Name cannot be blank.")
            continue

        # #can't be case sensitive. this messes up our user comfortability.
        matches = [ex for ex in master if query.lower() in ex.lower()]

        if not matches:
            print(f"  No matches for '{query}'. Try a different search or press Enter for custom.")
            continue

        # must show quantifiable outcome
        print(f"\n  Results for '{query}':")
        for i, name in enumerate(matches, 1):
            print(f"    {i}. {name}")
        print(f"    0. Search again")

        choice = input("\n  Pick a number (or 0 to search again): ").strip()

        # Validate the numeric choice
        if choice == "0":
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(matches):
            return matches[int(choice) - 1]

        print("  Invalid selection.")


def browse_catalog() -> str:
    """
    Show the full categorized catalog so users can browse without knowing
    what they're looking for first.  Returns the chosen exercise name.
    """
    categories = list(EXERCISE_CATALOG.keys())

    print("\n  ── Exercise Categories ──────────────────────")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")

    while True:
        cat_choice = input("\n  Pick a category (number): ").strip()
        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
            break
        print("  Invalid choice.")

    chosen_cat = categories[int(cat_choice) - 1]
    exercises  = EXERCISE_CATALOG[chosen_cat]

    print(f"\n  ── {chosen_cat} ──────────────────────")
    for i, ex in enumerate(exercises, 1):
        print(f"  {i}. {ex}")

    while True:
        ex_choice = input("\n  Pick an exercise (number): ").strip()
        if ex_choice.isdigit() and 1 <= int(ex_choice) <= len(exercises):
            return exercises[int(ex_choice) - 1]
        print("  Invalid choice.")


##  now we need a section to log bodyweight

def log_bodyweight(log: dict) -> None:
    """Prompt for today's bodyweight and append it to the log."""
    date = datetime.today().strftime("%Y-%m-%d")

    while True:
        try:
            weight = float(input("  Enter bodyweight (lbs): "))
            if weight <= 0:
                raise ValueError
            break
        except ValueError:
            print("  Please enter a positive number (e.g. 185.5).\n")

    log["bodyweight"].append({"date": date, "weight": weight})
    save_log(log)
    print(f"  ✓ Logged {weight} lbs on {date}.\n")


##,. again we want to log workout sessions as well


def log_workout(log: dict) -> None:
    """
    Guide the user through logging a full workout session.
    Each exercise is chosen via search or catalog browse (no raw typing)
    to eliminate case/typo mismatches.
    """
    date         = datetime.today().strftime("%Y-%m-%d")
    session_name = input("  Workout name (e.g. 'Push Day'): ").strip() or "Unnamed Session"
    exercises    = []

    print("\n  Add exercises. Choose 'Done' when finished.\n")

    while True:
        # Give the user three ways to pick an exercise
        print("  How would you like to add an exercise?")
        print("  1. Search by name")
        print("  2. Browse catalog by category")
        print("  3. Done — finish this session")
        pick = input("  → ").strip()

        if pick == "3" or pick.lower() in ("done", "d", ""):
            break
        elif pick == "1":
            exercise_name = search_exercise(log, prompt="Search exercise name")
        elif pick == "2":
            exercise_name = browse_catalog()
        else:
            print("  Invalid choice.\n")
            continue

        # Collect sets for this exercise
        sets = []
        while True:
            try:
                num_sets = int(input(f"\n  How many sets for {exercise_name}? "))
                if num_sets <= 0:
                    raise ValueError
                break
            except ValueError:
                print("  Please enter a positive whole number.")

        for i in range(1, num_sets + 1):
            while True:
                try:
                    reps   = int(input(f"    Set {i} — Reps: "))
                    weight = float(input(f"    Set {i} — Weight (lbs, 0 = bodyweight): "))
                    break
                except ValueError:
                    print("    Please enter valid numbers.")
            sets.append({"set": i, "reps": reps, "weight": weight})

        exercises.append({"exercise": exercise_name, "sets": sets})
        print(f"  ✓ {exercise_name} added.\n")

    if not exercises:
        print("  No exercises recorded. Session not saved.\n")
        return

    session = {"date": date, "name": session_name, "exercises": exercises}
    log["workouts"].append(session)
    save_log(log)
    print(f"  ✓ Workout '{session_name}' saved ({len(exercises)} exercise(s)).\n")


# fix this section to be the stats section that approporiate manages entries.


def show_bodyweight_stats(log: dict) -> None:
    """Display the full bodyweight history and net change."""
    entries = log["bodyweight"]
    if not entries:
        print("  No bodyweight data logged yet.\n")
        return

    print("\n  ── Bodyweight History ──────────────────────")
    for entry in entries:
        print(f"  {entry['date']}   {entry['weight']} lbs")

    if len(entries) > 1:
        first   = entries[0]["weight"]
        latest  = entries[-1]["weight"]
        change  = round(latest - first, 1)
        prefix  = "+" if change >= 0 else ""
        print(f"\n  Net change: {prefix}{change} lbs  ({entries[0]['date']} → {entries[-1]['date']})")
    print()


def show_workout_history(log: dict) -> None:
    """Print every logged workout session with per-set detail."""
    workouts = log["workouts"]
    if not workouts:
        print("  No workouts logged yet.\n")
        return

    print("\n  ── Workout History ─────────────────────────")
    for session in workouts:
        print(f"\n  [{session['date']}]  {session['name']}")
        for ex in session["exercises"]:
            # Condense all sets onto one readable line
            set_summary = ",  ".join(
                f"Set {s['set']}: {s['reps']} reps @ {s['weight']} lbs"
                for s in ex["sets"]
            )
            print(f"    {ex['exercise']}: {set_summary}")
    print()


def show_exercise_pr(log: dict) -> None:
    """
    Find the all-time heaviest single set for a searched exercise.
    Uses the search function so the exercise name always resolves correctly.
    """
    workouts = log["workouts"]
    if not workouts:
        print("  No workouts logged yet.\n")
        return

    exercise_name = search_exercise(log, prompt="Search exercise for PR lookup")

    best_weight = None
    best_date   = None

    for session in workouts:
        for ex in session["exercises"]:
            # Normalize to lowercase for comparison
            if ex["exercise"].lower() == exercise_name.lower():
                for s in ex["sets"]:
                    if best_weight is None or s["weight"] > best_weight:
                        best_weight = s["weight"]
                        best_date   = session["date"]

    if best_weight is None:
        print(f"  No data found for '{exercise_name}'.\n")
    else:
        print(f"\n  PR for '{exercise_name}': {best_weight} lbs  (logged on {best_date})\n")


##new charts will be added. user wiull find it appealing to the eye and may be increasingly motivated.



def chart_bodyweight(log: dict) -> None:
    """
    Plot bodyweight over time and save the chart as a PNG.
    This uses matplotlib, which was not covered in class — the new skill
    learned for this project.
    """
    if not CHARTS_AVAILABLE:
        print("  matplotlib is not installed. Run: pip install matplotlib\n")
        return

    entries = log["bodyweight"]
    if len(entries) < 2:
        print("  Need at least 2 bodyweight entries to generate a chart.\n")
        return

    # need to generate strings into Python date objects through matpotlib
    dates   = [datetime.strptime(e["date"], "%Y-%m-%d") for e in entries]
    weights = [e["weight"] for e in entries]

    fig, ax = plt.subplots(figsize=(10, 5))

    # line and scatters, so therefore individual data points are clearly visible
    ax.plot(dates, weights, color="#4A90D9", linewidth=2, label="Bodyweight")
    ax.scatter(dates, weights, color="#4A90D9", s=50, zorder=5)

    # Shade the area under the line for visual depth
    ax.fill_between(dates, weights, min(weights) - 2, alpha=0.15, color="#4A90D9")

    # ensure that the detes don'tr overlap, fix formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)

    ax.set_title("Bodyweight Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Weight (lbs)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    path = "bodyweight_chart.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    print(f"  ✓ Chart saved as '{path}'\n")


def chart_workout_volume(log: dict) -> None:
    """
    Plot total training volume (sum of sets × reps × weight) per session.
    Volume is a common proxy for workout intensity/effort in sports science.
    """
    if not CHARTS_AVAILABLE:
        print("  matplotlib is not installed. Run: pip install matplotlib\n")
        return

    workouts = log["workouts"]
    if len(workouts) < 2:
        print("  Need at least 2 workout sessions to generate a chart.\n")
        return

    dates   = []
    volumes = []

    for session in workouts:
        dates.append(datetime.strptime(session["date"], "%Y-%m-%d"))
        # Volume = Σ (reps × weight) across all sets and all exercises
        vol = sum(
            s["reps"] * s["weight"]
            for ex in session["exercises"]
            for s in ex["sets"]
        )
        volumes.append(vol)

    fig, ax = plt.subplots(figsize=(10, 5))

    # bar chart may be most visually ap[pealing for data comparison]
    bar_colors = ["#E07B54" if v == max(volumes) else "#5DAB8A" for v in volumes]
    ax.bar(dates, volumes, color=bar_colors, width=0.6, zorder=3)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)

    ax.set_title("Workout Volume per Session  (reps × weight, lbs)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Volume (lbs)")
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)

    # create a deep and condense session
    peak_idx = volumes.index(max(volumes))
    ax.text(
        dates[peak_idx], max(volumes) * 1.02,
        "Peak", ha="center", fontsize=9, color="#E07B54", fontweight="bold"
    )

    path = "volume_chart.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    print(f"  ✓ Chart saved as '{path}'\n")


# stats and progress as a sub menu

def show_stats_menu(log: dict) -> None:
    """Sub-menu that groups all viewing and charting options."""
    options = {
        "1": ("Bodyweight history (text)",            lambda: show_bodyweight_stats(log)),
        "2": ("Full workout history (text)",           lambda: show_workout_history(log)),
        "3": ("Personal record (PR) for an exercise", lambda: show_exercise_pr(log)),
        "4": ("📊 Chart: bodyweight over time",        lambda: chart_bodyweight(log)),
        "5": ("📊 Chart: workout volume per session",  lambda: chart_workout_volume(log)),
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
            options[choice][1]()
        else:
            print("  Invalid choice.\n")


# the main menu or entry point

def main() -> None:
    log = load_log()

    menu = {
        "1": ("Log bodyweight",   lambda: log_bodyweight(log)),
        "2": ("Log a workout",    lambda: log_workout(log)),
        "3": ("Stats & progress", lambda: show_stats_menu(log)),
    }

    print("\n══════════════════════════════════════")
    print("       Fitness Tracker CLI  v2")
    print("══════════════════════════════════════\n")

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
            menu[choice][1]()
        else:
            print("  Invalid choice — try again.\n")


if __name__ == "__main__":
    main()
