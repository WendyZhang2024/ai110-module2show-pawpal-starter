import datetime as dt

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state: the only place per-user data lives ---------------------
# Streamlit re-runs this whole script on every interaction. An Owner created
# at module scope would be rebuilt (and emptied) each time, so it is created
# once and then looked up in session state on every rerun.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner: Owner = st.session_state.owner
# Scheduler keeps no state of its own, so rebuilding it on every rerun is free.
scheduler = Scheduler(owner)

# A message queued by the Complete button, shown after the rerun it triggers.
flash = st.session_state.get("flash")
if flash:
    del st.session_state["flash"]

st.title("🐾 PawPal+")
st.caption("One daily care plan for every pet in the household.")

if flash:
    st.success(flash)

# --- Sidebar: who we are and who we look after -----------------------------
with st.sidebar:
    st.header("Your household")

    with st.form("owner_form"):
        owner_name = st.text_input("Owner name", value=owner.name)
        if st.form_submit_button("Save name"):
            owner.name = owner_name.strip() or owner.name

    with st.form("add_pet", clear_on_submit=True):
        new_pet_name = st.text_input("Pet name", value="Mochi")
        new_species = st.selectbox("Species", ["dog", "cat", "other"])
        if st.form_submit_button("Add pet"):
            owner.add_pet(Pet(new_pet_name, new_species))

    st.caption(
        f"{owner.name} · {len(owner.pets)} pet(s) · {owner.total_task_count()} task(s)"
    )
    for existing in owner.pets:
        st.markdown(f"- **{existing.name}** ({existing.species})")

    if st.button("Reset household"):
        del st.session_state.owner
        st.rerun()

if not owner.pets:
    st.info("Add a pet in the sidebar to get started.")
    st.stop()

# --- Add a task ------------------------------------------------------------
st.subheader("Schedule a task")

with st.form("add_task", clear_on_submit=True):
    pet_choice = st.selectbox("Pet", [pet.name for pet in owner.pets])
    description = st.text_input("What needs doing?", value="Morning walk")

    col_time, col_duration = st.columns(2)
    with col_time:
        start = st.time_input("Start time", value=dt.time(8, 0))
    with col_duration:
        duration = st.number_input(
            "Minutes", min_value=5, max_value=240, value=20, step=5
        )

    col_priority, col_repeat = st.columns(2)
    with col_priority:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col_repeat:
        frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])

    if st.form_submit_button("Add task"):
        if not description.strip():
            st.warning("Give the task a name first.")
        else:
            # st.time_input returns a datetime.time, but Task stores "HH:MM".
            owner.get_pet(pet_choice).add_task(
                Task(
                    description,
                    start.strftime("%H:%M"),
                    int(duration),
                    priority,
                    frequency,
                )
            )

# --- Everything currently on file ------------------------------------------
st.subheader("Tasks")

for pet in owner.pets:
    open_count = len(pet.get_tasks(completed=False))
    st.markdown(
        f"**{pet.name}** · {pet.species} · {open_count} open / {pet.task_count()} total"
    )
    if not pet.tasks:
        st.caption("No tasks yet.")
        continue

    for index, task in enumerate(pet.tasks):
        left, right = st.columns([6, 1], vertical_alignment="center")
        with left:
            line = (
                f"`{task.due_time}` **{task.description}** — "
                f"{task.duration_minutes} min · {task.priority}"
            )
            if task.frequency != "once":
                line += f" · repeats {task.frequency}"
            if task.due_date != dt.date.today():
                line += f" · {task.due_date:%a %d %b}"
            if task.completed:
                line += " · done"
            st.markdown(line)
        with right:
            if not task.completed:
                if st.button("Complete", key=f"complete-{pet.name}-{index}"):
                    next_task = scheduler.mark_task_complete(task)
                    if next_task is not None:
                        st.session_state.flash = (
                            f"'{task.description}' done — next one on "
                            f"{next_task.due_date:%A %d %B}."
                        )
                    st.rerun()

# --- Today's plan ----------------------------------------------------------
st.divider()
st.subheader("Today's plan")

col_order, col_pet = st.columns(2)
with col_order:
    order = st.segmented_control("Order by", ["Time", "Priority"], default="Time")
with col_pet:
    pet_filter = st.selectbox(
        "Show", ["All pets"] + [pet.name for pet in owner.pets]
    )

sort_key = "priority" if order == "Priority" else "time"
plan = scheduler.get_daily_plan(
    pet_name=None if pet_filter == "All pets" else pet_filter,
    sort=sort_key,
)

open_today = len(plan)
done_total = len(scheduler.filter_tasks(completed=True))

col_pets, col_open, col_done = st.columns(3)
col_pets.metric("Pets", len(owner.pets))
col_open.metric("Open today", open_today)
col_done.metric("Completed", done_total)

if plan:
    st.dataframe(
        [
            {
                "Time": task.due_time,
                "Pet": pet,
                "Task": task.description,
                "Minutes": task.duration_minutes,
                "Priority": task.priority,
                "Repeats": task.frequency,
            }
            for pet, task in plan
        ],
        hide_index=True,
    )
    st.caption(
        "Sorted by start time, across every pet."
        if sort_key == "time"
        else "Highest priority first, then earliest start."
    )
else:
    st.info("Nothing left to do today - every task is complete.")

# --- Conflicts -------------------------------------------------------------
conflicts = scheduler.detect_conflicts()
if conflicts:
    st.warning(
        "\n\n".join(conflicts),
        title=f"{len(conflicts)} scheduling conflict(s)",
    )
