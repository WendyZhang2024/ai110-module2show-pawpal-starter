"""PawPal+ core logic: Task, Pet, Owner and Scheduler.

Design reference: diagrams/uml.mmd

This module must stay UI-agnostic so that main.py (CLI) and app.py (Streamlit)
can both drive the same objects.

The Scheduler implements four algorithmic features, all of which read every
pet's tasks through Owner.tasks_with_pets():
    1. chronological sorting          sort_by_time()
    2. priority-first sorting         sort_by_priority()
    3. filtering by pet/status        filter_tasks()  + get_daily_plan()
    4. exact-time conflict warnings   detect_conflicts()
plus recurring tasks, which live on Task.mark_complete().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

TIME_FORMAT = "%H:%M"
PRIORITIES = ("low", "medium", "high")
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


@dataclass
class Task:
    """A single care activity for one pet."""

    description: str
    due_time: str = "09:00"
    duration_minutes: int = 15
    priority: str = "medium"
    frequency: str = "once"
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate the fields that the scheduler relies on."""
        self.frequency = str(self.frequency).strip().lower()
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}")
        self.priority = str(self.priority).strip().lower()
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}")
        if isinstance(self.due_date, str):
            self.due_date = date.fromisoformat(self.due_date)

    def time_minutes(self) -> int:
        """Return the due time as minutes since midnight, for sorting."""
        hours, minutes = self.due_time.split(":")
        return int(hours) * 60 + int(minutes)

    def mark_complete(self) -> Task | None:
        """Mark the task done and return the next occurrence if it recurs."""
        self.completed = True
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        return Task(
            description=self.description,
            due_time=self.due_time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            due_date=self.due_date + timedelta(days=days),
        )


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str = "dog"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> Task:
        """Attach a task to this pet and return it."""
        self.tasks.append(task)
        return task

    def remove_task(self, task: Task) -> bool:
        """Remove a task from this pet, returning True when it was found."""
        # Identity check, not equality: dataclasses generate __eq__, so
        # task "in" self.tasks would also match a *different* task that
        # happens to have identical fields.
        for index, existing in enumerate(self.tasks):
            if existing is task:
                del self.tasks[index]
                return True
        return False

    def task_count(self) -> int:
        """Return how many tasks this pet has."""
        return len(self.tasks)

    def get_tasks(self, completed: bool | None = None) -> list[Task]:
        """Return this pet's tasks, optionally filtered by completion."""
        if completed is None:
            return list(self.tasks)
        return [task for task in self.tasks if task.completed is completed]


@dataclass
class Owner:
    """The pet owner: the single entry point to every pet and task."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> Pet:
        """Add a pet to this owner and return it."""
        self.pets.append(pet)
        return pet

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with this name, or None when it is unknown."""
        for pet in self.pets:
            if pet.name.lower() == name.strip().lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across every pet as one flat list."""
        # Two loops in one comprehension: for each pet, then each of its tasks.
        return [task for pet in self.pets for task in pet.tasks]

    def total_task_count(self) -> int:
        """Return how many tasks the household has in total."""
        return len(self.get_all_tasks())

    def tasks_with_pets(self) -> list[tuple[str, Task]]:
        """Return (pet_name, task) pairs for the whole household.

        The Scheduler reads from this instead of looping over pets itself, so
        every scheduling decision sees every pet's tasks.
        """
        return [(pet.name, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """The brain: filters, sorts and validates tasks across all pets."""

    owner: Owner

    def _entries(self) -> list[tuple[str, Task]]:
        """Collect every (pet_name, task) pair through the Owner."""
        return self.owner.tasks_with_pets()

    def sort_by_time(
        self, entries: list[tuple[str, Task]] | None = None
    ) -> list[tuple[str, Task]]:
        """Order tasks chronologically by their HH:MM due time."""
        source = self._entries() if entries is None else list(entries)
        return sorted(
            source,
            key=lambda entry: (entry[1].time_minutes(), entry[0].lower()),
        )

    def sort_by_priority(
        self, entries: list[tuple[str, Task]] | None = None
    ) -> list[tuple[str, Task]]:
        """Order tasks by priority (high first), then by due time."""
        source = self._entries() if entries is None else list(entries)
        return sorted(
            source,
            key=lambda entry: (
                -PRIORITY_RANK[entry[1].priority],
                entry[1].time_minutes(),
                entry[0].lower(),
            ),
        )

    def filter_tasks(
        self,
        entries: list[tuple[str, Task]] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
        priority: str | None = None,
    ) -> list[tuple[str, Task]]:
        """Keep the tasks that match every filter which was supplied."""
        source = self._entries() if entries is None else list(entries)
        wanted_pet = pet_name.strip().lower() if pet_name else None
        wanted_priority = priority.strip().lower() if priority else None

        kept: list[tuple[str, Task]] = []
        for owner_name, task in source:
            if wanted_pet and owner_name.lower() != wanted_pet:
                continue
            if completed is not None and task.completed is not completed:
                continue
            if wanted_priority and task.priority != wanted_priority:
                continue
            kept.append((owner_name, task))
        return kept

    def detect_conflicts(
        self, entries: list[tuple[str, Task]] | None = None
    ) -> list[str]:
        """Return a warning per pair of unfinished tasks sharing a start time.

        This is a lightweight check: two tasks conflict when they fall on the
        same day at exactly the same HH:MM. It reports instead of raising, so
        one bad slot never breaks the whole plan.
        """
        source = self._entries() if entries is None else list(entries)
        pending = [
            (pet_name, task) for pet_name, task in source if not task.completed
        ]

        warnings: list[str] = []
        for index, (pet_a, task_a) in enumerate(pending):
            for pet_b, task_b in pending[index + 1 :]:
                if task_a.due_date != task_b.due_date:
                    continue
                if task_a.due_time != task_b.due_time:
                    continue
                warnings.append(
                    f"Conflict at {task_a.due_time} on "
                    f"{task_a.due_date.isoformat()}: '{task_a.description}' "
                    f"({pet_a}) and '{task_b.description}' ({pet_b}) are both booked."
                )
        return warnings

    def get_daily_plan(
        self,
        target_date: date | None = None,
        pet_name: str | None = None,
        sort: str = "time",
    ) -> list[tuple[str, Task]]:
        """Return one day's unfinished tasks, filtered and sorted for display."""
        day = target_date or date.today()
        entries = self.filter_tasks(pet_name=pet_name, completed=False)
        entries = [(pet, task) for pet, task in entries if task.due_date == day]
        if sort == "priority":
            return self.sort_by_priority(entries)
        return self.sort_by_time(entries)

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task and file its next occurrence under the same pet."""
        pet = self._find_pet_for(task)
        next_task = task.mark_complete()
        if next_task is not None and pet is not None:
            pet.add_task(next_task)
        return next_task

    def _find_pet_for(self, task: Task) -> Pet | None:
        """Return the pet that owns this task, or None when it is orphaned."""
        for pet in self.owner.pets:
            if any(existing is task for existing in pet.tasks):
                return pet
        return None
