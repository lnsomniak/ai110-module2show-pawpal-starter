"""Pytest test suite for PawPal+ scheduling system."""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# -- Fixtures --------------------------------------------------


@pytest.fixture
def sample_task() -> Task:
    """Return a basic daily task for testing."""
    return Task(
        description="Morning walk",
        time="07:00",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet_name="Mandy",
    )


@pytest.fixture
def sample_pet() -> Pet:
    """Return a pet with no tasks."""
    return Pet(name="Mandy", species="Dog")


@pytest.fixture
def loaded_owner() -> Owner:
    """Return an owner with two pets and several tasks."""
    owner = Owner(name="Sergio")

    mandy = Pet(name="Mandy", species="Dog")
    miso = Pet(name="Miso", species="Cat")

    mandy.add_task(Task(
        description="Morning walk",
        time="07:00",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet_name="Mandy",
    ))
    mandy.add_task(Task(
        description="Evening walk",
        time="18:00",
        duration_minutes=30,
        priority="medium",
        frequency="daily",
        pet_name="Mandy",
    ))
    miso.add_task(Task(
        description="Clean litter box",
        time="09:00",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        pet_name="Miso",
    ))
    miso.add_task(Task(
        description="Vet checkup",
        time="14:00",
        duration_minutes=60,
        priority="high",
        frequency="once",
        pet_name="Miso",
    ))

    owner.add_pet(mandy)
    owner.add_pet(miso)
    return owner


# -- Task Tests ------------------------------------------------


def test_task_completion(sample_task: Task) -> None:
    """Verify mark_complete() changes task status from False to True."""
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_task_default_date(sample_task: Task) -> None:
    """Verify a new task defaults to today's date."""
    assert sample_task.task_date == date.today()


# -- Pet Tests -------------------------------------------------


def test_add_task_to_pet(sample_pet: Pet, sample_task: Task) -> None:
    """Verify adding a task increases pet's task count."""
    assert sample_pet.get_task_count() == 0
    sample_pet.add_task(sample_task)
    assert sample_pet.get_task_count() == 1


def test_pet_pending_and_completed(sample_pet: Pet) -> None:
    """Verify pending/completed filtering on a pet."""
    t1 = Task("Walk", "07:00", 30, "high", "daily", "Mandy")
    t2 = Task("Feed", "08:00", 10, "medium", "daily", "Mandy", completed=True)
    sample_pet.add_task(t1)
    sample_pet.add_task(t2)

    assert len(sample_pet.get_pending_tasks()) == 1
    assert len(sample_pet.get_completed_tasks()) == 1


def test_pet_no_tasks_returns_empty(sample_pet: Pet) -> None:
    """Edge case: pet with no tasks returns empty list."""
    assert sample_pet.get_pending_tasks() == []
    assert sample_pet.get_completed_tasks() == []
    assert sample_pet.get_task_count() == 0


# -- Owner Tests -----------------------------------------------


def test_owner_no_pets_returns_empty_tasks() -> None:
    """Edge case: owner with no pets returns empty task list."""
    owner = Owner(name="Empty")
    assert owner.get_all_tasks() == []


def test_get_pet_by_name(loaded_owner: Owner) -> None:
    """Verify get_pet_by_name finds the right pet (case-insensitive)."""
    pet = loaded_owner.get_pet_by_name("mandy")
    assert pet is not None
    assert pet.name == "Mandy"


def test_get_pet_by_name_not_found(loaded_owner: Owner) -> None:
    """Verify get_pet_by_name returns None for unknown pet."""
    assert loaded_owner.get_pet_by_name("Ghost") is None


# -- Scheduler: Sorting ----------------------------------------


def test_sorting_correctness(loaded_owner: Owner) -> None:
    """Verify tasks returned in chronological order after sort_by_time()."""
    scheduler = Scheduler(loaded_owner)
    sorted_tasks = scheduler.sort_by_time()
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_priority(loaded_owner: Owner) -> None:
    """Verify high-priority tasks come before low-priority tasks."""
    scheduler = Scheduler(loaded_owner)
    sorted_tasks = scheduler.sort_by_priority()
    priorities = [t.priority for t in sorted_tasks]

    # Find first non-high and verify no high comes after it
    seen_non_high = False
    for p in priorities:
        if p != "high":
            seen_non_high = True
        if seen_non_high and p == "high":
            pytest.fail("High-priority task found after a lower-priority task")


# -- Scheduler: Filtering --------------------------------------


def test_filter_by_pet(loaded_owner: Owner) -> None:
    """Verify filtering returns only tasks for the specified pet."""
    scheduler = Scheduler(loaded_owner)
    mandy_tasks = scheduler.filter_by_pet("Mandy")

    assert len(mandy_tasks) == 2
    assert all(t.pet_name == "Mandy" for t in mandy_tasks)


def test_filter_by_status(loaded_owner: Owner) -> None:
    """Verify filtering by completed/pending works."""
    scheduler = Scheduler(loaded_owner)

    pending = scheduler.filter_by_status(completed=False)
    assert len(pending) == 4  # all tasks start as pending

    completed = scheduler.filter_by_status(completed=True)
    assert len(completed) == 0

    # Mark one complete
    pending[0].mark_complete()
    assert len(scheduler.filter_by_status(completed=True)) == 1
    assert len(scheduler.filter_by_status(completed=False)) == 3


# -- Scheduler: Conflicts --------------------------------------


def test_conflict_detection() -> None:
    """Verify scheduler flags two tasks at the same time."""
    owner = Owner(name="Test")
    dog = Pet(name="Rex", species="Dog")
    cat = Pet(name="Whiskers", species="Cat")

    dog.add_task(Task("Walk Rex", "09:00", 30, "high", "daily", "Rex"))
    cat.add_task(Task("Feed Whiskers", "09:00", 10, "medium", "daily", "Whiskers"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "09:00" in conflicts[0]


def test_no_conflicts(loaded_owner: Owner) -> None:
    """Verify no false-positive conflicts when times are unique."""
    scheduler = Scheduler(loaded_owner)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 0


# -- Scheduler: Recurrence -------------------------------------


def test_recurrence_logic_daily() -> None:
    """Confirm marking a daily task complete creates a new task for the following day."""
    owner = Owner(name="Test")
    pet = Pet(name="Buddy", species="Dog")
    task = Task("Walk", "07:00", 30, "high", "daily", "Buddy")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    original_date = task.task_date
    new_task = scheduler.mark_task_complete(task)

    assert task.completed is True
    assert new_task is not None
    assert new_task.completed is False
    assert new_task.task_date == original_date + timedelta(days=1)
    assert pet.get_task_count() == 2


def test_recurrence_logic_weekly() -> None:
    """Confirm marking a weekly task complete creates one for +7 days."""
    owner = Owner(name="Test")
    pet = Pet(name="Buddy", species="Dog")
    task = Task("Grooming", "10:00", 45, "low", "weekly", "Buddy")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    original_date = task.task_date
    new_task = scheduler.mark_task_complete(task)

    assert new_task is not None
    assert new_task.task_date == original_date + timedelta(days=7)


def test_once_task_no_recurrence() -> None:
    """Confirm marking a one-time task complete does NOT create a new task."""
    owner = Owner(name="Test")
    pet = Pet(name="Buddy", species="Dog")
    task = Task("Vet visit", "14:00", 60, "high", "once", "Buddy")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    new_task = scheduler.mark_task_complete(task)

    assert task.completed is True
    assert new_task is None
    assert pet.get_task_count() == 1
