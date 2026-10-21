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

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
