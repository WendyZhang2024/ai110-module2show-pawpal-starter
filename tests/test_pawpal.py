"""Tests for the PawPal+ logic layer.

Run with:

    python -m pytest

Phase 2 covers the data layer and time sorting. Sorting by priority, filtering,
conflict detection, recurrence and JSON persistence get their tests in
Phases 4-5 as those features are implemented.
"""

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture()
def household() -> Owner:
    """One owner, two pets, three tasks added deliberately out of time order."""
    jordan = Owner("Jordan")
    biscuit = jordan.add_pet(Pet("Biscuit", "dog"))
    mochi = jordan.add_pet(Pet("Mochi", "cat"))

    biscuit.add_task(Task("Evening walk", "18:30", 30, "medium"))
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high"))
    mochi.add_task(Task("Feeding", "07:30", 10, "high"))

    return jordan


def test_mark_complete_changes_status() -> None:
    """mark_complete() flips the completion flag."""
    task = Task("Meds", "09:15", 5, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_task_count() -> None:
    """Adding a task to a pet raises that pet's task count."""
    pet = Pet("Biscuit", "dog")
    assert pet.task_count() == 0

    pet.add_task(Task("Morning walk", "08:00"))

    assert pet.task_count() == 1


@pytest.mark.parametrize(
    ("due_time", "expected"),
    [("08:00", 480), ("9:05", 545), ("23:59", 1439)],
)
def test_time_minutes_converts_hh_mm(due_time: str, expected: int) -> None:
    """HH:MM becomes minutes since midnight, which is what sorting uses."""
    assert Task("Walk", due_time).time_minutes() == expected


def test_sort_by_time_orders_tasks_chronologically(household: Owner) -> None:
    """The scheduler returns tasks earliest-first, across both pets."""
    times = [task.due_time for _, task in Scheduler(household).sort_by_time()]

    assert times == ["07:30", "08:00", "18:30"]


def test_sort_by_time_actually_reorders_the_input(household: Owner) -> None:
    """The sort is not a no-op: the entered order differs from the result."""
    entered = [task.due_time for _, task in household.tasks_with_pets()]
    sorted_times = [task.due_time for _, task in Scheduler(household).sort_by_time()]

    assert entered != sorted_times


def test_sort_by_time_spans_multiple_pets(household: Owner) -> None:
    """Scheduling works on the whole household, not one pet at a time."""
    pets = {pet_name for pet_name, _ in Scheduler(household).sort_by_time()}

    assert pets == {"Biscuit", "Mochi"}


def test_get_all_tasks_aggregates_every_pet(household: Owner) -> None:
    """Owner.get_all_tasks() flattens both pets' task lists."""
    descriptions = {task.description for task in household.get_all_tasks()}

    assert len(household.get_all_tasks()) == 3
    assert descriptions == {"Evening walk", "Morning walk", "Feeding"}


def test_tasks_with_pets_keeps_the_pet_name(household: Owner) -> None:
    """Each pair carries the pet it belongs to, so warnings can name it."""
    pairs = household.tasks_with_pets()

    assert ("Mochi", household.get_pet("Mochi").tasks[0]) in pairs
    assert ("Biscuit", household.get_pet("Biscuit").tasks[0]) in pairs


def test_get_tasks_filters_by_completion() -> None:
    """completed=False / True split a pet's tasks correctly."""
    pet = Pet("Mochi", "cat")
    pending = Task("Feeding", "07:30")
    finished = Task("Grooming", "11:00")
    finished.mark_complete()
    pet.add_task(pending)
    pet.add_task(finished)

    assert pet.get_tasks(completed=False) == [pending]
    assert pet.get_tasks(completed=True) == [finished]
    assert len(pet.get_tasks()) == 2


def test_remove_task_reports_missing_task() -> None:
    """Removing something the pet does not have returns False, not an error."""
    pet = Pet("Mochi")

    assert pet.remove_task(Task("Ghost walk")) is False


def test_remove_task_matches_by_identity_not_fields() -> None:
    """Two tasks with identical fields are still different tasks."""
    pet = Pet("Mochi")
    first = Task("Walk", "07:00")
    twin = Task("Walk", "07:00")  # same fields, different object
    pet.add_task(first)
    pet.add_task(twin)

    assert pet.remove_task(first) is True
    assert pet.task_count() == 1
    assert pet.tasks[0] is twin


def test_get_pet_handles_case_and_whitespace(household: Owner) -> None:
    """Lookup is forgiving, and unknown names return None instead of raising."""
    assert household.get_pet("  MOCHI ").name == "Mochi"
    assert household.get_pet("nobody") is None
