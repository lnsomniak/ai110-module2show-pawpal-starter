"""PawPal+ CLI demo -- demonstrates core scheduling features in the terminal."""

from pawpal_system import Task, Pet, Owner, Scheduler
from datetime import date


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 56}")
    print(f"  {title}")
    print(f"{'=' * 56}")


def print_task(task: Task, index: int = 0) -> None:
    """Print a single task in a readable format."""
    status = "[DONE]" if task.completed else "[    ]"
    priority_tag = {"high": "[HIGH]", "medium": "[MED ]", "low": "[LOW ]"}.get(
        task.priority, "[??? ]"
    )
    print(
        f"  {index:>2}. {status} [{task.time}] {priority_tag} {task.description} "
        f"-- {task.pet_name} ({task.duration_minutes} min, {task.frequency})"
    )


def main() -> None:
    """Run the PawPal+ CLI demo."""

    # -- Create owner and pets ---------------------------------
    owner = Owner(name="Sergio")

    mandy = Pet(name="Mandy", species="Dog")
    miso = Pet(name="Miso", species="Cat")

    owner.add_pet(mandy)
    owner.add_pet(miso)

    # -- Add tasks ---------------------------------------------
    mandy.add_task(Task(
        description="Morning walk",
        time="07:00",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet_name="Mandy",
    ))
    mandy.add_task(Task(
        description="Give heartworm medication",
        time="08:00",
        duration_minutes=5,
        priority="high",
        frequency="weekly",
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
        description="Brush fur",
        time="18:00",  # same time as Mandy's evening walk -- conflict!
        duration_minutes=15,
        priority="low",
        frequency="weekly",
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

    scheduler = Scheduler(owner)

    # -- 1. Today's Schedule (sorted by time) ------------------
    print_header("PawPal+ -- Today's Schedule")
    print(f"  Owner: {owner.name} | Date: {date.today()}")
    print(f"  Pets: {', '.join(p.name for p in owner.pets)}")
    print(f"  Total tasks: {len(scheduler.get_all_tasks())}")
    print()

    for i, task in enumerate(scheduler.sort_by_time(), 1):
        print_task(task, i)

    # -- 2. Conflict Detection ---------------------------------
    print_header("Conflict Detection")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts detected.")

    # -- 3. Sort by Priority -----------------------------------
    print_header("Tasks Sorted by Priority")
    for i, task in enumerate(scheduler.sort_by_priority(), 1):
        print_task(task, i)

    # -- 4. Filter by Pet --------------------------------------
    print_header("Mandy's Tasks Only")
    for i, task in enumerate(scheduler.filter_by_pet("Mandy"), 1):
        print_task(task, i)

    print_header("Miso's Tasks Only")
    for i, task in enumerate(scheduler.filter_by_pet("Miso"), 1):
        print_task(task, i)

    # -- 5. Recurring Task Logic -------------------------------
    print_header("Recurring Task Demo")
    daily_task = mandy.get_pending_tasks()[0]  # Morning walk
    print(f"  Completing: '{daily_task.description}' (frequency: {daily_task.frequency})")
    print(f"  Original date: {daily_task.task_date}")

    new_task = scheduler.mark_task_complete(daily_task)
    print(f"  -> Marked complete!")

    if new_task:
        print(f"  -> New occurrence created for: {new_task.task_date}")
        print(f"     Task: '{new_task.description}' at {new_task.time}")
    print(f"  Mandy's total tasks now: {mandy.get_task_count()}")

    # -- 6. Filter by Status -----------------------------------
    print_header("Filter by Status")
    pending = scheduler.filter_by_status(completed=False)
    completed = scheduler.filter_by_status(completed=True)
    print(f"  Pending tasks: {len(pending)}")
    print(f"  Completed tasks: {len(completed)}")
    print()
    print("  Completed:")
    for i, task in enumerate(completed, 1):
        print_task(task, i)

    print(f"\n{'=' * 56}")
    print("  PawPal+ demo complete.")
    print(f"{'=' * 56}\n")


if __name__ == "__main__":
    main()
