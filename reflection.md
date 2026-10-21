# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My first design split the system into four classes, one per responsibility:

- **Task** — one care activity. Holds `description`, `due_time` (`"HH:MM"`),
  `duration_minutes`, `priority` and `completed`. `time_minutes()` converts the
  time string into minutes past midnight so tasks can be compared numerically,
  and `mark_complete()` flips the completion flag.
- **Pet** — identity (`name`, `species`) plus the list of tasks that belong to
  it, with the methods to manage that list: `add_task`, `remove_task`,
  `task_count`, `get_tasks`.
- **Owner** — identity plus a list of pets, and one aggregation method,
  `get_all_tasks()`, that flattens every pet's tasks into a single list.
- **Scheduler** — holds an `Owner` and does the planning: sorting, filtering
  and conflict detection. It stores no tasks of its own.

The three core actions I designed for a user were: add a pet, schedule a care
task for a pet, and see today's tasks in time order.

Two decisions shaped everything after that. First, `Task` deliberately does not
store which pet it belongs to — the `Pet` owns its task list, so every task has
exactly one home and the `Scheduler` never has to keep two copies in sync.
Second, `Scheduler` reads tasks only through `Owner.get_all_tasks()`, never from
a single `Pet`. That is what makes "plan the whole household's day" possible and
lets conflict detection compare one pet's walk against another pet's feeding.
I kept `due_time` as a string instead of a datetime because plain string
comparison sorts `"9:00"` after `"10:00"`; a small `time_minutes()` helper keeps
the stored data simple while giving the scheduler a correct sort key.

**b. Design changes**

Yes — two things changed once real logic met the design.

1. **`Owner` grew a second aggregation method.** The first design only had
   `get_all_tasks()`, returning one flat list of tasks. That was enough to sort
   a plan, but not enough to *name* anything: a conflict warning has to say
   "`Meds` (Biscuit) clashes with `Play session` (Mochi)", and filtering by pet
   needs the pet's name attached to each task. The flat list had already thrown
   that information away. I added `Owner.tasks_with_pets()` returning
   `(pet_name, task)` pairs, and made it the only collection the `Scheduler`
   reads from. `get_all_tasks()` stayed, because counting and simple tests still
   want the flat view.
2. **`Task` gained `frequency` and `due_date`.** Neither existed in the first
   UML, because the first version of the system had no concept of "which day is
   this" or "does this repeat" — a task was just a description with a time.
   Supporting recurring tasks forced both fields in: a `daily` task needs to
   know the date it belongs to so the next occurrence can be computed with
   `timedelta(days=1)`. Adding `due_date` also made `get_daily_plan()` honest —
   it now genuinely filters to one calendar day instead of assuming "everything
   in the list is today".

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers six things: which pet the task belongs to, its start
time, its duration, its priority, whether it repeats, and whether it is already
done.

I ranked them by what a pet owner can least afford to get wrong. **Start time**
is the backbone — the output is a timeline, and a timeline that is not in
chronological order is broken no matter what. **Completion** comes next: a
finished task must never appear in today's plan, so completion is a filter
before anything else is ordered. **Priority** is the ordering *preference*
layered on top of the timeline; it decides what to do first when the owner has
more to do than hours, but it must not silently reorder the day's fixed points
(medication at 09:15 is 09:15 even if it is low priority). **Pet** is a filter
the reader chooses, not a constraint the scheduler imposes, because the whole
point of the app is planning the household together. **Duration** is stored but
deliberately not scheduled against available time yet — that is the next
iteration, and pretending otherwise would be a plan the app cannot keep.

**b. Tradeoffs**

The scheduler only flags a conflict when two tasks start at **exactly** the same
`HH:MM`; it does not check whether their durations overlap. A 20-minute task at
09:15 and a 30-minute task at 09:25 overlap by 10 minutes in reality, and this
scheduler will not warn about them.

That is a real gap, and it is a deliberate one. Overlap detection requires
deciding what "overlapping" means when durations are guesses: a 20-minute walk
that takes 35 minutes would silently invalidate every computed overlap after it,
and the plan would start warning about clashes that are not real. Exact-start
matching has the opposite failure mode — it never invents a conflict, and it
only ever *under*-reports. For a first version I preferred a detector that is
always believable to one that is more thorough but occasionally wrong: a warning
that fires on a false positive teaches the owner to ignore warnings entirely,
which is worse than no warning at all.

The same tradeoff keeps the algorithm honest and cheap. Comparing every pair is
`O(n²)`, which is fine for a household's handful of tasks per day and would need
bucketing by time if the data grew. And because `detect_conflicts()` returns
warning strings instead of raising, a clash can never take down the plan — the
owner still gets a schedule, plus an explanation of what to fix.

---

## 3. AI Collaboration

**a. How you used AI**

I used the assistant in three modes, and the balance shifted as the project went on.

- **Design partner.** I described the scenario and asked how to split it into
  classes and where the "planning" responsibility should live. The four-class
  split — and the rule that `Scheduler` reads through `Owner` instead of
  touching a `Pet` directly — came out of that conversation.
- **Reviewer.** After a file was written I asked for a review rather than more
  code: "what is missing here, what will break?" That is how the aggregation
  gap surfaced: `Owner` only returned a flat task list, but conflict warnings
  need pet names, so `tasks_with_pets()` was added.
- **Debugger of its own output.** Several assistant-written snippets failed the
  moment they ran (an import of a package that was not installed, a chained
  `add_pet(...).add_pet(...)` call that returned a `Pet`). Running the code was
  the only way to catch that.

The narrow prompts were the useful ones — "review this file for missing
relationships or logic bottlenecks", "what edge cases would break this
scheduler?" Broad prompts like "build the app" produced code I could not
explain, so I stopped using them.

**b. Judgment and verification**

I did not accept the assistant's proposal to import `tabulate` inside
`pawpal_system.py` for terminal formatting. It assumed the package was
available; running `main.py` produced `ModuleNotFoundError`. Since readable
terminal output does not require a dependency, I kept the logic layer
dependency-free and formatted with f-strings, and deferred `tabulate` to an
optional extension instead.

I also removed a `next_available_slot()` method that the assistant had put in
the UML draft but never implemented. Rather than leave the diagram ahead of the
code, I deleted it — the rubric asks for a UML that matches the final
implementation.

For anything else, I checked by running it instead of trusting the
explanation: small `python -c` scripts per class, then the pytest suite after
every change. The identity test is the clearest case. I confirmed in the REPL
that two `Task` objects with identical fields compare equal with `==`, which is
why `remove_task` compares with `is`, and why there is a permanent regression
test holding that behaviour in place.


---

## 4. Testing and Verification

**a. What you tested**

Forty cases across five behaviours, plus the edge cases that usually break a
scheduler.

- **Task lifecycle** — completing a task flips its status; a `once` task has no
  successor; `daily` schedules tomorrow and `weekly` schedules seven days out;
  the new occurrence is filed under the *right* pet.
- **Ordering** — chronological across every pet, and priority-first with time
  breaking ties. One test asserts the sorted output differs from the input, so
  a sort that silently does nothing cannot pass.
- **Filtering and the daily plan** — by pet, by status, by priority, and all
  three combined; the plan excludes other days and completed tasks.
- **Conflict detection** — same pet, across pets, ignoring completed tasks, and
  a test that pins the method to *return* messages rather than raise.
- **Data integrity** — identity-based removal, cross-household aggregation,
  forgiving pet lookup.
- **Edge cases** — a pet with no tasks, a household with no pets, an unknown pet
  name, a day with nothing scheduled, invalid `priority`/`frequency`.

These mattered because the UI only ever exercises the happy path. Writing the
suite immediately paid for itself: the "complete the same daily task twice"
test failed on the first run and exposed a real bug — two identical tasks were
being created for tomorrow. Nothing in the browser could reach that path, which
is exactly the point: tests cover what the *code* can do, not what a user
happens to click. The identity-removal test is the same idea in reverse: it
locks in a behaviour that is easy to "simplify" back into a bug.

**b. Confidence**

**4 out of 5.** Every documented rule has at least one test, the conflict
detector's promise never to raise is itself tested, and the one bug the suite
found is fixed and pinned by a regression test.

The missing star is duration. The scheduler compares start times only, so a
20-minute task at 09:15 and a 30-minute task at 09:25 overlap in reality without
being flagged, and nothing checks whether the day's tasks fit into the hours the
owner actually has. Those are real gaps, but they are *documented* gaps — the
tradeoff is written down rather than hidden.

If I had more time I would test: overlapping durations (which needs a decision
about what counts as overlap), a task whose duration runs past midnight, the
DST changeover where the clock hour repeats, and a few hundred tasks to confirm
the pairwise conflict check stays fast enough.

---

## 5. Reflection

**a. What went well**

The part I am most satisfied with is that the logic layer never depended on the
UI. `main.py` printed a correct, sorted, conflict-warning plan before `app.py`
existed, and the exact same objects then ran inside Streamlit unchanged. That
turned the UI phase into wiring rather than debugging, and it meant that when
something looked wrong in the browser I already knew the backend was sound.

The second thing I would protect is the identity-based removal. It looked like
a fussy detail at the time — "surely removing by value is fine" — but the
scenario where it matters (two tasks with identical fields) is exactly the
scenario a pet owner creates by repeating the same care task twice in a day.
Writing the regression test is what stopped that decision from being quietly
simplified back into a bug.

**b. What you would improve**

Duration. Right now a task's duration is stored and displayed but never actually
used to plan anything: the scheduler does not check whether the day's tasks fit
the hours the owner has, and conflicts are start-time only. The next iteration
would compute free slots between a day's start and end and fit tasks into them
by priority, which also fixes the overlap blind spot.

After that: date navigation (the app only ever plans today), persistence so a
browser refresh does not wipe the household, and grouping the task list by day
once a pet has more than a handful of tasks.

**c. Key takeaway**

An AI assistant is confident in proportion to how *plausible* something sounds,
not how *true* it is. In one session it imported a package that was not
installed, and wrote a call chain that contradicted the API it had itself
designed twenty minutes earlier — both looked completely reasonable on the page.
The habit that caught every one of those was cheap and non-negotiable: run the
thing immediately, and treat "it looks right" as the start of verification
rather than the end of it.

The deeper lesson is about who owns the judgement. Decisions like "a conflict
means the same start minute, not overlapping durations" are design decisions,
not implementation details. If the human does not make them explicitly, the
assistant's default silently becomes the system's behaviour — and then nobody can
explain why the app does what it does.
