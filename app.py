"""PawPal+ -- Streamlit UI for smart pet care scheduling."""

import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

# -- Page Config -----------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon=None, layout="wide")

# -- Session State Init ----------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False

# -- Sidebar: Owner & Pet Setup --------------------------------

with st.sidebar:
    st.header("PawPal+ Setup")

    # Owner setup
    st.subheader("Owner Info")
    owner_name = st.text_input("Your name", value="Sergio")
    if st.button("Set Owner", use_container_width=True):
        if owner_name.strip():
            st.session_state.owner = Owner(name=owner_name.strip())
            st.session_state.schedule_generated = False
            st.success(f"Owner set: {owner_name}")
        else:
            st.warning("Please enter a name.")

    if st.session_state.owner:
        st.divider()
        st.subheader("Add a Pet")
        pet_name = st.text_input("Pet name")
        pet_species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Fish", "Rabbit", "Other"])
        if st.button("Add Pet", use_container_width=True):
            if pet_name.strip():
                existing = st.session_state.owner.get_pet_by_name(pet_name.strip())
                if existing:
                    st.warning(f"'{pet_name}' already exists.")
                else:
                    new_pet = Pet(name=pet_name.strip(), species=pet_species)
                    st.session_state.owner.add_pet(new_pet)
                    st.success(f"Added {pet_species} '{pet_name}'!")
            else:
                st.warning("Please enter a pet name.")

        # Show current pets
        if st.session_state.owner.pets:
            st.divider()
            st.subheader("Your Pets")
            for pet in st.session_state.owner.pets:
                pending = len(pet.get_pending_tasks())
                st.write(f"- **{pet.name}** ({pet.species}) -- {pending} pending task(s)")

# -- Main Content ----------------------------------------------

st.title("PawPal+")
st.caption("Smart pet care scheduling -- sort, filter, detect conflicts, and automate recurring tasks.")

if not st.session_state.owner:
    st.info("Set your name in the sidebar to get started.")
    st.stop()

owner: Owner = st.session_state.owner

if not owner.pets:
    st.info("Add at least one pet in the sidebar to continue.")
    st.stop()

# -- Add Task Form ---------------------------------------------

st.header("Add a Task")

pet_names = [p.name for p in owner.pets]

with st.form("add_task_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        task_pet = st.selectbox("Assign to pet", pet_names)
        task_desc = st.text_input("Task description", placeholder="e.g. Morning walk")
        task_time = st.time_input("Scheduled time")
    with col2:
        task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=15)
        task_priority = st.selectbox("Priority", ["high", "medium", "low"])
        task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    submitted = st.form_submit_button("Add Task", use_container_width=True)
    if submitted:
        if task_desc.strip():
            time_str = task_time.strftime("%H:%M")
            new_task = Task(
                description=task_desc.strip(),
                time=time_str,
                duration_minutes=int(task_duration),
                priority=task_priority,
                frequency=task_frequency,
                pet_name=task_pet,
            )
            pet = owner.get_pet_by_name(task_pet)
            if pet:
                pet.add_task(new_task)
                st.success(f"Added '{task_desc}' for {task_pet} at {time_str}")
        else:
            st.warning("Please enter a task description.")

# -- Schedule Display ------------------------------------------

scheduler = Scheduler(owner)
all_tasks = scheduler.get_all_tasks()

if not all_tasks:
    st.info("No tasks yet -- add some above!")
    st.stop()

st.divider()
st.header("Today's Schedule")

# Filters
col_f1, col_f2 = st.columns(2)
with col_f1:
    filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
with col_f2:
    filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"], key="filter_status")

# Generate schedule button
if st.button("Generate Schedule", use_container_width=True, type="primary"):
    st.session_state.schedule_generated = True

if st.session_state.schedule_generated:
    # Apply filters
    tasks = scheduler.sort_by_time()
    if filter_pet != "All":
        tasks = [t for t in tasks if t.pet_name == filter_pet]
    if filter_status == "Pending":
        tasks = [t for t in tasks if not t.completed]
    elif filter_status == "Completed":
        tasks = [t for t in tasks if t.completed]

    # Conflict warnings
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            st.warning(warning)

    if not tasks:
        st.info("No tasks match the current filters.")
    else:
        # Build table data
        priority_labels = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
        table_data = []
        for t in tasks:
            table_data.append({
                "Status": "Done" if t.completed else "Pending",
                "Time": t.time,
                "Task": t.description,
                "Pet": t.pet_name,
                "Priority": priority_labels.get(t.priority, t.priority),
                "Duration": f"{t.duration_minutes} min",
                "Frequency": t.frequency.capitalize(),
            })

        st.table(table_data)

    # -- Task Completion ---------------------------------------
    st.divider()
    st.subheader("Complete a Task")

    pending_tasks = scheduler.filter_by_status(completed=False)
    if pending_tasks:
        task_options = {
            f"[{t.time}] {t.description} ({t.pet_name})": t
            for t in pending_tasks
        }
        selected_label = st.selectbox("Select a task to complete", list(task_options.keys()))
        if st.button("Mark Complete", use_container_width=True):
            selected_task = task_options[selected_label]
            new_task = scheduler.mark_task_complete(selected_task)
            st.success(f"Completed: '{selected_task.description}'")
            if new_task:
                st.info(
                    f"Recurring task created for {new_task.task_date}: "
                    f"'{new_task.description}' at {new_task.time}"
                )
            st.rerun()
    else:
        st.success("All tasks are completed!")

    # -- Priority View -----------------------------------------
    st.divider()
    st.subheader("Priority View")
    priority_sorted = scheduler.sort_by_priority()
    if filter_pet != "All":
        priority_sorted = [t for t in priority_sorted if t.pet_name == filter_pet]

    priority_data = []
    for t in priority_sorted:
        priority_data.append({
            "Priority": priority_labels.get(t.priority, t.priority),
            "Time": t.time,
            "Task": t.description,
            "Pet": t.pet_name,
            "Status": "Done" if t.completed else "Pending",
        })
    if priority_data:
        st.table(priority_data)
