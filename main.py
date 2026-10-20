"""PawPal+ command-line demo.

Phase 2, Step 2: a temporary "testing ground" that proves the logic layer works
before any UI exists. Run it with:

    python main.py

This file is a throwaway harness for the scheduler - it is never imported by
app.py. Its terminal output is the evidence that the backend behaves correctly,
and a copy of it lives in README.md under "Sample Output".
"""

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_owner() -> Owner:
    """Create the demo household: one owner, two pets, five tasks."""
    owner = Owner("Jordan")

    biscuit = owner.add_pet(Pet("Biscuit", "dog"))
    mochi = owner.add_pet(Pet("Mochi", "cat"))

    # Added deliberately out of time order so the sort has something to fix.
    biscuit.add_task(Task("Evening walk", "18:30", 30, "medium"))
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high"))
    mochi.add_task(Task("Feeding", "07:30", 10, "high"))
    mochi.add_task(Task("Play session", "12:00", 20, "low"))
    biscuit.add_task(Task("Meds", "09:15", 5, "high"))

    return owner


def print_table(entries: list[tuple[str, Task]], title: str) -> None:
    """Print (pet_name, task) pairs as aligned columns."""
    print(title)
    print("-" * 62)
    for pet_name, task in entries:
        line = (
            f"  {task.due_time}  {pet_name:<8} {task.description:<16} "
            f"{task.duration_minutes:>3} min  {task.priority}"
        )
        print(line.rstrip())
    print()


def main() -> None:
    """Build the demo household and print today's schedule."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print()
    print("PawPal+ - today's schedule")
    print("=" * 62)
    print(f"Owner: {owner.name}")
    print(f"Tasks in the system: {owner.total_task_count()}")
    print()

    print_table(owner.tasks_with_pets(), "As entered (out of time order):")
    print_table(scheduler.sort_by_time(), "Today's Schedule (sorted by time):")

    print("Tasks per pet:")
    print("-" * 62)
    for pet in owner.pets:
        print(f"  {pet.name:<8} {pet.species:<6} {pet.task_count()} task(s)")
    print()

    print("Logic layer verified. Next: wire this into the Streamlit UI (Phase 3).")


if __name__ == "__main__":
    main()
