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

## ✨ Features

**What the owner can do**

- Add pets (name + species) and see the household update immediately; the data
  survives every button click.
- Schedule a task per pet with a start time, duration, priority and repeat mode
  (`once`, `daily`, `weekly`).
- Read today's plan as a single timeline across every pet, ordered either by
  time or by priority.
- Complete a task. A recurring task queues its next occurrence and tells you the
  date it landed on.
- Filter the plan to one pet, and get a warning when two tasks collide.
- Reset the household to start a clean demo.

**The algorithms behind it**

- `Scheduler.sort_by_time()` — chronological across every pet, with ties broken
  deterministically.
- `Scheduler.sort_by_priority()` — high → medium → low, then earliest start time.
- `Scheduler.filter_tasks()` / `get_daily_plan()` — filter by pet, completion
  status and priority; the plan keeps one calendar day of unfinished work.
- `Scheduler.detect_conflicts()` — reports unfinished tasks booked at the same
  exact minute, including across different pets.
- `Task.mark_complete()` — recurrence via `timedelta`, and idempotent, so
  completing the same task twice never duplicates tomorrow's copy.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run it

```bash
streamlit run app.py    # the interactive UI (http://localhost:8501)
python main.py          # the terminal demo, no browser needed
python -m pytest -q     # the test suite (40 cases)
```

The app starts with an empty household: add a pet in the sidebar first, then
schedule tasks for it. `main.py` needs no arguments and prints the same
behaviours to a terminal, which is a quick way to check the logic without a
browser.

## 🖥️ Sample Output

Terminal output of `python main.py` — one owner, two pets, five tasks added
deliberately out of time order, including a cross-pet time clash and a daily
task:

```
PawPal+ - today's schedule
======================================================================
Owner: Jordan
Pets: Biscuit, Mochi
Tasks in the system: 5

As entered (out of time order):
----------------------------------------------------------------------
  18:30  Biscuit  Evening walk      30 min  medium
  08:00  Biscuit  Morning walk      30 min  high
  09:15  Biscuit  Meds               5 min  high
  09:15  Mochi    Play session      20 min  low
  07:30  Mochi    Feeding           10 min  high   repeats daily

Today's plan (sorted by time):
----------------------------------------------------------------------
  07:30  Mochi    Feeding           10 min  high   repeats daily
  08:00  Biscuit  Morning walk      30 min  high
  09:15  Biscuit  Meds               5 min  high
  09:15  Mochi    Play session      20 min  low
  18:30  Biscuit  Evening walk      30 min  medium

Same tasks, highest priority first:
----------------------------------------------------------------------
  07:30  Mochi    Feeding           10 min  high   repeats daily
  08:00  Biscuit  Morning walk      30 min  high
  09:15  Biscuit  Meds               5 min  high
  18:30  Biscuit  Evening walk      30 min  medium
  09:15  Mochi    Play session      20 min  low

Conflict check:
----------------------------------------------------------------------
  ! Conflict at 09:15 on 2026-10-21: 'Meds' (Biscuit) and 'Play session' (Mochi) are both booked.

Recurring task check:
----------------------------------------------------------------------
  Completing 'Feeding' (daily) ...
  next occurrence: 2026-10-22 at 07:30
  today's plan still covers today only: True

Tasks per pet (tomorrow's feeding is already on file):
----------------------------------------------------------------------
  Biscuit  dog    3 task(s)
  Mochi    cat    3 task(s)

Logic layer verified. Run `streamlit run app.py` for the full UI.
```


## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest -q

# With coverage (needs `pip install pytest-cov`):
python -m pytest --cov=. --cov-report=term-missing
```

`python -m pytest` is used instead of plain `pytest` because it puts the project
root on `sys.path`; `tests/conftest.py` makes the bare command work too.

What the 40 cases cover: task completion and counting, identity-based removal,
time conversion, chronological sorting across pets, priority sorting with time
tie-breaks, filtering by pet/status/priority, conflict detection (same pet,
across pets, ignoring completed tasks), daily and weekly recurrence with
idempotent completion, the daily plan's date + completion filtering, and the
edge cases that tend to break schedulers — a pet with no tasks, a household
with no pets, an unknown pet name, a day with nothing scheduled, and invalid
priority/frequency values.

Sample test output:

```
$ python -m pytest -q
........................................                                 [100%]
40 passed in 0.06s
```

**Confidence level: 4/5.** The sorting, filtering, recurrence and conflict rules
are each pinned by at least one test, and the identity-removal behaviour has a
dedicated regression test. The missing star is duration overlap: a 20-minute task
at 09:15 and a 30-minute task at 09:25 are not reported as a clash (see the
tradeoff in `reflection.md`), and nothing yet checks that a day's tasks fit into
the owner's available hours.


## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Compares `Task.time_minutes()` rather than the `"HH:MM"` text, because `"9:00" > "10:00"` as a string. Ties break on pet name so output is stable. |
| Sorting by priority | `Scheduler.sort_by_priority()` | high → medium → low, then earliest start time within a level. Works across every pet. |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.get_daily_plan()` | Filters by pet name, completion status and priority (all optional, combined with AND). The daily plan keeps only today's unfinished tasks. |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags two unfinished tasks booked on the same day at exactly the same `HH:MM` — including tasks belonging to different pets. Returns warning strings instead of raising, so one bad slot never breaks a plan. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.mark_task_complete()` | `daily` → next day, `weekly` → next week, computed with `timedelta`. The new occurrence is filed back under the same pet by the scheduler. |


## 📸 Demo Walkthrough

1. Start the app with `streamlit run app.py`. Add a pet in the sidebar — name it
   `Biscuit`, species `dog` — and it appears in the household list with the
   pet/task counters.
2. In **Schedule a task**, pick the pet, describe the task, set the start time,
   the duration, the priority and whether it repeats (`once`, `daily`,
   `weekly`). Submit.
3. Add `Morning walk` at 08:00 (high) and then `Evening walk` at 18:30
   (medium). Today's plan re-sorts on every submit, so the earlier task is
   always on top.
4. Switch **Order by** from `Time` to `Priority`: the high-priority tasks move
   to the top regardless of the clock, with time only breaking ties.
5. Schedule a second task at a time that is already taken (for example `Meds`
   at 09:15 and `Play session` on another pet at 09:15). A conflict warning
   names both tasks, both pets and the clashing time — nothing crashes.
6. Press **Complete** on a `daily` task. A success message names the date of
   the next occurrence, the task drops out of today's plan, and tomorrow's copy
   is already on file under the same pet.
7. Use **Show** to filter the plan down to a single pet, and **Reset
   household** in the sidebar to start over.

The same behaviours are visible without a browser by running `python main.py`
(see Sample Output above).

**Screenshot or video:** not included — the numbered walkthrough above plus the
CLI sample output are the demo.
