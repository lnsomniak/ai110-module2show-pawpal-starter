# PawPal+ -- Reflection

## 1. System Design

### 1a. Initial Design
I designed PawPal+ around four classes: **Task**, **Pet**, **Owner**, and **Scheduler**. `Task` is a Python dataclass holding scheduling attributes like time, duration, priority, frequency, and a `completed` flag. `Pet` is also a dataclass that owns a list of `Task` objects and provides convenience methods for counting and filtering its tasks. `Owner` manages a collection of `Pet` objects and can aggregate all tasks across them. `Scheduler` is the algorithmic engine -- it takes an `Owner` and provides sorting, filtering, conflict detection, and recurring task logic. Using dataclasses for `Task` and `Pet` kept the code concise and gave me `__init__`, `__repr__`, and equality checks for free.

### 1b. Design Changes
Originally, the `Scheduler` was going to maintain its own internal list of tasks. I changed this so that `Scheduler` dynamically pulls tasks from the `Owner`'s pets every time a method is called. This keeps the data in sync -- if a task is added to a pet after the scheduler is created, the scheduler automatically sees it without needing a manual refresh. I also added a `pet_name` field directly to `Task` so that filtering by pet could work without traversing the pet-task relationship every time.

## 2. Algorithm Design

### 2a. Constraints and Priorities
The `Scheduler` considers three dimensions when organizing tasks: **time of day** (chronological ordering), **priority level** (high, medium, low), and **task frequency** (once, daily, weekly). Priority was weighted as the most important factor in `sort_by_priority()` because medical tasks like giving heartworm medication absolutely cannot be skipped or deprioritized. Time serves as the tiebreaker within the same priority tier.

### 2b. Tradeoffs
Conflict detection currently only checks for **exact time matches** -- two tasks both at `09:00` will be flagged, but a 60-minute task at `09:00` and a 10-minute task at `09:30` will not, even though they overlap. I made this tradeoff intentionally: exact-match detection is simple, reliable, and sufficient for an MVP. Implementing duration-aware overlap would require converting `HH:MM` strings into datetime ranges and checking intersections, which adds complexity that was not justified for this iteration.

## 3. AI-Assisted Development

### 3a. How I Used AI
I used VS Code Copilot throughout development for several tasks:
- **Brainstorming**: Asked it to suggest a class structure for a pet scheduling app -- it helped me converge on the four-class design.
- **UML generation**: Prompted "generate a Mermaid class diagram for these 4 classes with these attributes" and got a working diagram on the first try.
- **Scaffolding**: Used Copilot to generate the initial dataclass skeletons, which I then filled in with real logic.
- **Tests**: Asked it to generate pytest tests for each method, then reviewed and adjusted assertions.
- **Formatting**: Got help with clean terminal output formatting in `main.py` using f-strings and tag indicators.

The most effective prompts were specific and scoped, like "generate a Mermaid class diagram for these 4 classes with these attributes" rather than vague requests like "help me build a pet app."

### 3b. Judgment and Verification
Copilot initially suggested putting all scheduling logic (sorting, filtering, conflict detection) directly inside the `Owner` class. I rejected this because it violates the **single-responsibility principle** -- `Owner` should manage pets, not implement scheduling algorithms. I moved all scheduling methods into a dedicated `Scheduler` class instead. This made the code more modular and testable: I can test scheduling logic independently of pet/owner management.

## 4. Testing

### 4a. What I Tested
My test suite covers:
- **Task completion**: Verifying `mark_complete()` flips the status
- **Task addition**: Confirming `add_task()` increments the pet's count
- **Sort correctness**: Checking chronological and priority ordering
- **Recurrence**: Ensuring daily tasks generate a +1 day copy and weekly tasks generate +7 days
- **Conflict detection**: Confirming two same-time tasks produce a warning
- **Filtering**: By pet name and by completion status
- **Edge cases**: Empty pet (no tasks) and empty owner (no pets)

This coverage matters because scheduling bugs in a pet care app could lead to missed medications or feedings -- the stakes are higher than a typical to-do list.

### 4b. Confidence
**4/5 stars**. Core logic is thoroughly tested and all tests pass. The gap is in duration-aware conflict detection (which is not implemented yet) and stress testing with large numbers of pets and tasks. I would also want integration tests for the Streamlit UI in a future iteration.

## 5. Reflection

### 5a. What Went Well
The **CLI-first approach** was the best decision I made. Building and verifying all logic in `main.py` before touching the Streamlit UI meant I could see results instantly in the terminal, catch bugs early, and iterate fast. By the time I wired up `app.py`, the backend was already solid and the UI work was purely about presentation.

### 5b. What I Would Improve
Two main additions: (1) **Duration-aware conflict detection** -- instead of just checking exact time matches, compute time ranges and check for overlaps. (2) **Data persistence** -- save the owner's data to a JSON file so tasks survive across app restarts. Currently everything resets when the Streamlit app reruns.

### 5c. Key Takeaway
AI tools like Copilot are powerful for scaffolding and generating boilerplate, but the **human architect** needs to enforce good design principles. Copilot does not inherently understand separation of concerns or know your system's design philosophy -- it just generates plausible code. The most important skill is knowing when to accept, modify, or reject what the AI suggests.
