"""Tests for the PawPal+ logic layer.

Run with:

    python -m pytest

The suite covers the data layer, the four scheduling algorithms (time sort,
priority sort, filtering, conflict detection) and recurring tasks. JSON
persistence tests live next to the persistence feature.
"""

from datetime import date, timedelta

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


# --- data layer ------------------------------------------------------------


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


# --- sorting ---------------------------------------------------------------


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


def test_sort_by_priority_puts_high_first(household: Owner) -> None:
    """High priority sorts before medium, whatever the clock says."""
    household.get_pet("Biscuit").add_task(Task("Brushing", "07:00", 10, "low"))

    priorities = [
        task.priority for _, task in Scheduler(household).sort_by_priority()
    ]

    assert priorities == ["high", "high", "medium", "low"]


def test_sort_by_priority_breaks_ties_by_time(household: Owner) -> None:
    """Two high-priority tasks are still ordered by start time."""
    times = [
        task.due_time
        for _, task in Scheduler(household).sort_by_priority()
        if task.priority == "high"
    ]

    assert times == ["07:30", "08:00"]


# --- filtering -------------------------------------------------------------


def test_filter_tasks_by_pet(household: Owner) -> None:
    """Only the named pet's tasks are kept."""
    kept = Scheduler(household).filter_tasks(pet_name="mochi")

    assert [task.description for _, task in kept] == ["Feeding"]


def test_filter_tasks_by_completion(household: Owner) -> None:
    """Completed and pending tasks are separated."""
    feeding = household.get_pet("Mochi").tasks[0]
    feeding.mark_complete()
    scheduler = Scheduler(household)

    assert [t.description for _, t in scheduler.filter_tasks(completed=True)] == [
        "Feeding"
    ]
    assert len(scheduler.filter_tasks(completed=False)) == 2


def test_filter_tasks_by_priority(household: Owner) -> None:
    """Priority filtering keeps only the matching level."""
    kept = Scheduler(household).filter_tasks(priority="high")

    assert {task.description for _, task in kept} == {"Morning walk", "Feeding"}


def test_filter_tasks_combines_filters(household: Owner) -> None:
    """Every supplied filter has to match at once."""
    kept = Scheduler(household).filter_tasks(pet_name="Biscuit", priority="high")

    assert [task.description for _, task in kept] == ["Morning walk"]


# --- conflict detection ----------------------------------------------------


def test_detect_conflicts_flags_same_time_same_day() -> None:
    """Two pending tasks at the same minute are reported."""
    owner = Owner("Jordan")
    biscuit = owner.add_pet(Pet("Biscuit", "dog"))
    biscuit.add_task(Task("Meds", "09:15", 5, "high"))
    biscuit.add_task(Task("Breakfast", "09:15", 10, "medium"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "09:15" in warnings[0]
    assert "Meds" in warnings[0] and "Breakfast" in warnings[0]


def test_detect_conflicts_spans_pets() -> None:
    """A clash between two different pets is still a clash."""
    owner = Owner("Jordan")
    owner.add_pet(Pet("Biscuit", "dog")).add_task(Task("Meds", "09:15"))
    owner.add_pet(Pet("Mochi", "cat")).add_task(Task("Play", "09:15"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "Biscuit" in warnings[0] and "Mochi" in warnings[0]


def test_detect_conflicts_ignores_completed_tasks() -> None:
    """A finished task cannot clash with anything."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "cat"))
    done = pet.add_task(Task("Feeding", "07:30"))
    pet.add_task(Task("Play", "07:30"))
    done.mark_complete()

    assert Scheduler(owner).detect_conflicts() == []


def test_detect_conflicts_ignores_different_times(household: Owner) -> None:
    """Distinct start times produce no warnings."""
    assert Scheduler(household).detect_conflicts() == []


def test_detect_conflicts_reports_instead_of_raising() -> None:
    """Conflicts come back as messages, so one bad slot never crashes a plan."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "cat"))
    pet.add_task(Task("Feeding", "07:30"))
    pet.add_task(Task("Play", "07:30"))

    result = Scheduler(owner).detect_conflicts()

    assert isinstance(result, list)
    assert isinstance(result[0], str)


# --- daily plan ------------------------------------------------------------


def test_get_daily_plan_excludes_other_days(household: Owner) -> None:
    """Tomorrow's tasks do not leak into today's plan."""
    mochi = household.get_pet("Mochi")
    mochi.add_task(Task("Vet visit", "10:00", 60, "high", due_date=date.today() + timedelta(days=1)))

    plan = Scheduler(household).get_daily_plan()

    assert "Vet visit" not in [task.description for _, task in plan]
    assert len(plan) == 3


def test_get_daily_plan_excludes_completed(household: Owner) -> None:
    """Done tasks disappear from the plan."""
    household.get_pet("Mochi").tasks[0].mark_complete()

    plan = Scheduler(household).get_daily_plan()

    assert [task.description for _, task in plan] == ["Morning walk", "Evening walk"]


def test_get_daily_plan_can_sort_by_priority(household: Owner) -> None:
    """The plan honours the requested ordering."""
    plan = Scheduler(household).get_daily_plan(sort="priority")

    assert [task.priority for _, task in plan] == ["high", "high", "medium"]


def test_get_daily_plan_filters_by_pet(household: Owner) -> None:
    """A single-pet plan contains only that pet's tasks."""
    plan = Scheduler(household).get_daily_plan(pet_name="Biscuit")

    assert {pet_name for pet_name, _ in plan} == {"Biscuit"}
    assert len(plan) == 2


# --- recurring tasks -------------------------------------------------------


def test_mark_complete_once_returns_none() -> None:
    """A one-off task has no next occurrence."""
    assert Task("Vet visit", "11:00", 60, "high").mark_complete() is None


def test_mark_complete_daily_returns_next_day() -> None:
    """A daily task schedules the same time tomorrow."""
    task = Task("Feeding", "07:30", 10, "high", "daily")

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.due_time == "07:30"
    assert next_task.completed is False


def test_mark_complete_weekly_returns_next_week() -> None:
    """A weekly task schedules the same time seven days out."""
    task = Task("Bath", "15:00", 45, "medium", "weekly")

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=7)


def test_scheduler_files_next_occurrence_under_same_pet() -> None:
    """The scheduler puts tomorrow's task back on the right pet."""
    owner = Owner("Jordan")
    biscuit = owner.add_pet(Pet("Biscuit", "dog"))
    mochi = owner.add_pet(Pet("Mochi", "cat"))
    feeding = mochi.add_task(Task("Feeding", "07:30", 10, "high", "daily"))

    next_task = Scheduler(owner).mark_task_complete(feeding)

    assert next_task is not None
    assert mochi.task_count() == 2
    assert biscuit.task_count() == 0
    assert mochi.tasks[-1] is next_task


# --- edge cases ------------------------------------------------------------


def test_pet_with_no_tasks_returns_empty_list() -> None:
    """A pet that was never given a task reports nothing, not an error."""
    pet = Pet("Biscuit", "dog")

    assert pet.get_tasks() == []
    assert pet.get_tasks(completed=False) == []
    assert pet.task_count() == 0


def test_empty_household_scheduler_returns_nothing() -> None:
    """Every scheduler method is safe on an owner who has no pets yet."""
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)

    assert owner.get_all_tasks() == []
    assert scheduler.sort_by_time() == []
    assert scheduler.sort_by_priority() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.get_daily_plan() == []


def test_filter_by_unknown_pet_returns_nothing(household: Owner) -> None:
    """An unknown pet name filters everything out instead of raising."""
    assert Scheduler(household).filter_tasks(pet_name="Rex") == []


def test_daily_plan_for_a_day_with_nothing(household: Owner) -> None:
    """A day with no scheduled tasks gives an empty plan."""
    tomorrow = date.today() + timedelta(days=1)

    assert Scheduler(household).get_daily_plan(target_date=tomorrow) == []


@pytest.mark.parametrize(
    ("field", "value"), [("priority", "urgent"), ("frequency", "hourly")]
)
def test_invalid_task_fields_raise(field: str, value: str) -> None:
    """A bad priority or frequency fails loudly at construction time."""
    with pytest.raises(ValueError):
        Task("Walk", "08:00", 30, **{field: value})


def test_completing_a_task_twice_does_not_duplicate_the_next_occurrence() -> None:
    """Marking the same daily task complete twice must not create two copies."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "cat"))
    feeding = mochi.add_task(Task("Feeding", "07:30", 10, "high", "daily"))
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(feeding)
    scheduler.mark_task_complete(feeding)

    assert mochi.task_count() == 2  # today's task + exactly one tomorrow
