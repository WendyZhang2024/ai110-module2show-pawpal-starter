"""PawPal+ core logic: Task, Pet, Owner and Scheduler.

Design reference: diagrams/uml.mmd

This module must stay UI-agnostic so that main.py (CLI) and app.py (Streamlit)
can both drive the same objects.

Step 3: the data layer (Task, Pet, Owner) is implemented. The Scheduler is
still a skeleton and fills in during Steps 4-5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    """A single care activity for one pet."""

    description: str
    due_time: str = "09:00"
    duration_minutes: int = 15
    priority: str = "medium"
    completed: bool = False

    def time_minutes(self) -> int:
        """Return the due time as minutes since midnight, for sorting."""
        hours, minutes = self.due_time.split(":")
        return int(hours) * 60 + int(minutes)

    def mark_complete(self) -> Task | None:
        """Mark the task done and return the next occurrence if it recurs."""
        self.completed = True
        # Step 5 adds daily/weekly recurrence here: return the next Task
        # instead of None when this task repeats.
        return None


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
        raise NotImplementedError("Scheduler.sort_by_priority (Step 4)")

    def filter_tasks(
        self,
        entries: list[tuple[str, Task]] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
        priority: str | None = None,
    ) -> list[tuple[str, Task]]:
        """Keep the tasks that match every filter which was supplied."""
        raise NotImplementedError("Scheduler.filter_tasks (Step 4)")

    def detect_conflicts(
        self, entries: list[tuple[str, Task]] | None = None
    ) -> list[str]:
        """Return a warning per pair of unfinished tasks sharing a start time."""
        raise NotImplementedError("Scheduler.detect_conflicts (Step 5)")

    def get_daily_plan(
        self,
        target_date: date | None = None,
        pet_name: str | None = None,
    ) -> list[tuple[str, Task]]:
        """Return one day's unfinished tasks, filtered and sorted for display."""
        raise NotImplementedError("Scheduler.get_daily_plan (Step 5)")

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
