"""PawPal+ core logic layer -- Task, Pet, Owner, and Scheduler classes."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    """Represents a single pet-care task with scheduling metadata."""

    description: str
    time: str  # "HH:MM" 24-hour format
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    frequency: str  # "once", "daily", "weekly"
    pet_name: str
    completed: bool = False
    task_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    """Represents a pet belonging to an owner."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def get_task_count(self) -> int:
        """Return the total number of tasks for this pet."""
        return len(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        """Return all completed tasks for this pet."""
        return [t for t in self.tasks if t.completed]


@dataclass
class Owner:
    """Represents a pet owner who manages one or more pets."""

    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's collection."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all pets."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_pet_by_name(self, name: str) -> Optional[Pet]:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None


class Scheduler:
    """Scheduling engine that operates on an Owner's pets and tasks."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        """Initialize the scheduler with an owner."""
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks from the owner's pets."""
        return self.owner.get_all_tasks()

    def sort_by_time(self) -> List[Task]:
        """Return tasks sorted chronologically by HH:MM time string."""
        return sorted(self.get_all_tasks(), key=lambda t: t.time)

    def sort_by_priority(self) -> List[Task]:
        """Return tasks sorted by priority (high first), then by time."""
        return sorted(
            self.get_all_tasks(),
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 99), t.time),
        )

    def filter_by_status(self, completed: bool) -> List[Task]:
        """Return tasks filtered by completion status."""
        return [t for t in self.get_all_tasks() if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return tasks filtered by pet name."""
        return [
            t
            for t in self.get_all_tasks()
            if t.pet_name.lower() == pet_name.lower()
        ]

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for tasks scheduled at the same time."""
        time_map: dict[str, List[Task]] = {}
        for task in self.get_all_tasks():
            time_map.setdefault(task.time, []).append(task)

        warnings: List[str] = []
        for time_str, tasks in sorted(time_map.items()):
            if len(tasks) > 1:
                names = ", ".join(
                    f"'{t.description}' ({t.pet_name})" for t in tasks
                )
                warnings.append(
                    f"WARNING -- Conflict at {time_str}: {names}"
                )
        return warnings

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete and create the next occurrence if recurring."""
        task.mark_complete()

        if task.frequency in ("daily", "weekly"):
            delta = timedelta(days=1) if task.frequency == "daily" else timedelta(days=7)
            new_task = Task(
                description=task.description,
                time=task.time,
                duration_minutes=task.duration_minutes,
                priority=task.priority,
                frequency=task.frequency,
                pet_name=task.pet_name,
                completed=False,
                task_date=task.task_date + delta,
            )
            # Add the new task to the correct pet
            pet = self.owner.get_pet_by_name(task.pet_name)
            if pet is not None:
                pet.add_task(new_task)
            return new_task
        return None

    def get_daily_schedule(self) -> dict:
        """Return sorted tasks for the day with conflict warnings."""
        return {
            "tasks": self.sort_by_time(),
            "conflicts": self.detect_conflicts(),
        }
