# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## 🏗️ Implementation Summary

PawPal+ is one logic layer plus two thin drivers:

| Layer | File | Job |
|---|---|---|
| Logic | `pawpal_system.py` | Every rule lives here. No Streamlit, no printing. |
| Terminal demo | `main.py` | Builds a household and prints the plan. Never imported by the app. |
| UI | `app.py` | Collects input and calls the logic. Holds no rules of its own. |

Four classes, one responsibility each, wired in a single direction — the drivers talk to `Scheduler`, `Scheduler` talks to `Owner`, `Owner` talks to `Pet`, and every `Pet` owns its own `Task` list:

- **Task** — one activity: description, `due_time` (`"HH:MM"`), duration, priority, completion state. `time_minutes()` exists because `"9:00"` sorts *after* `"10:00"` when compared as text.
- **Pet** — identity (name, species) plus its own task list, and the methods that manage it.
- **Owner** — identity plus pets, and `tasks_with_pets()` / `get_all_tasks()`, the only ways the scheduler is allowed to read data. That indirection is what lets a plan cover the whole household instead of one pet at a time.
- **Scheduler** — reads through the Owner, never keeps a copy of a task, and returns `(pet_name, task)` pairs so every result still knows whose task it is.

Because the `Scheduler` stores no state of its own, there is exactly one source of truth for the data: the UI can be replaced and the logic still works.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Terminal output of `python main.py` — one owner, two pets, five tasks added
deliberately out of time order, then the same tasks sorted by `Scheduler`:

```
PawPal+ - today's schedule
==============================================================
Owner: Jordan
Tasks in the system: 5

As entered (out of time order):
--------------------------------------------------------------
  18:30  Biscuit  Evening walk      30 min  medium
  08:00  Biscuit  Morning walk      30 min  high
  09:15  Biscuit  Meds               5 min  high
  07:30  Mochi    Feeding           10 min  high
  12:00  Mochi    Play session      20 min  low

Today's Schedule (sorted by time):
--------------------------------------------------------------
  07:30  Mochi    Feeding           10 min  high
  08:00  Biscuit  Morning walk      30 min  high
  09:15  Biscuit  Meds               5 min  high
  12:00  Mochi    Play session      20 min  low
  18:30  Biscuit  Evening walk      30 min  medium

Tasks per pet:
--------------------------------------------------------------
  Biscuit  dog    3 task(s)
  Mochi    cat    2 task(s)

Logic layer verified. Next: wire this into the Streamlit UI (Phase 3).
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
