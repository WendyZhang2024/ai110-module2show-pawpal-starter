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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
