"""PawPal+ command-line demo.

Phase 2-4 testing ground: proves the logic layer works before the UI is
trusted. Run it with:

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
    biscuit.add_task(Task("Meds", "09:15", 5, "high"))
    # 09:15 clashes with Biscuit's meds - a conflict across two pets.
    mochi.add_task(Task("Play session", "09:15", 20, "low"))
    # A daily task, so completing it must schedule tomorrow's feeding.
    mochi.add_task(Task("Feeding", "07:30", 10, "high", "daily"))

    return owner


def print_table(entries: list[tuple[str, Task]], title: str) -> None:
    """Print (pet_name, task) pairs as aligned columns."""
    print(title)
    print("-" * 70)
    if not entries:
        print("  (nothing scheduled)")
    for pet_name, task in entries:
        line = (
            f"  {task.due_time}  {pet_name:<8} {task.description:<16} "
            f"{task.duration_minutes:>3} min  {task.priority:<6}"
        )
        if task.frequency != "once":
            line += f" repeats {task.frequency}"
        print(line.rstrip())
    print()


def main() -> None:
    """Build the demo household and exercise every scheduling feature."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print()
    print("PawPal+ - today's schedule")
    print("=" * 70)
    print(f"Owner: {owner.name}")
    print(f"Pets: {', '.join(pet.name for pet in owner.pets)}")
    print(f"Tasks in the system: {owner.total_task_count()}")
    print()

    print_table(owner.tasks_with_pets(), "As entered (out of time order):")
    print_table(scheduler.get_daily_plan(), "Today's plan (sorted by time):")
    print_table(
        scheduler.sort_by_priority(scheduler.filter_tasks(completed=False)),
        "Same tasks, highest priority first:",
    )

    print("Conflict check:")
    print("-" * 70)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for message in conflicts:
            print(f"  ! {message}")
    else:
        print("  no conflicts found")
    print()

    print("Recurring task check:")
    print("-" * 70)
    feeding = owner.get_pet("Mochi").tasks[-1]
    print(f"  Completing '{feeding.description}' ({feeding.frequency}) ...")
    next_feeding = scheduler.mark_task_complete(feeding)
    if next_feeding is not None:
        print(
            f"  next occurrence: {next_feeding.due_date.isoformat()} "
            f"at {next_feeding.due_time}"
        )
    plan_dates = {task.due_date for _, task in scheduler.get_daily_plan()}
    print(f"  today's plan still covers today only: {plan_dates <= {feeding.due_date}}")
    print()

    print("Tasks per pet (tomorrow's feeding is already on file):")
    print("-" * 70)
    for pet in owner.pets:
        print(f"  {pet.name:<8} {pet.species:<6} {pet.task_count()} task(s)")
    print()

    print("Logic layer verified. Run `streamlit run app.py` for the full UI.")


if __name__ == "__main__":
    main()
