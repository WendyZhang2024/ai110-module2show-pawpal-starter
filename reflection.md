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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
