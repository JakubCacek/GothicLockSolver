"""
Created on Sun Jun  7 13:45:52 2026

@author: JakubCacek
"""

import json
from collections import deque
from typing import List, Dict, Any, Optional

import pandas as pd
import streamlit as st

n_locks = 5
min_pos = 1
max_pos = 7
target = 4
max_states = 20000


# ============================================================
# Solver logic
# ============================================================

def state_key(position: List[int]) -> str:
    return "-".join(map(str, position))


def parse_state_key(key: str) -> List[int]:
    return [int(x) for x in key.split("-")]


def apply_lock_move(
    problem: Dict[str, Any],
    position: List[int],
    selected_lock: int,
    click_direction: str
) -> Dict[str, Any]:
    """
    click_direction is what the player clicks in the game: "L" or "R".

    Gothic logic:
    L click -> physical movement to the right (+1)
    R click -> physical movement to the left (-1)
    """

    if click_direction not in ["L", "R"]:
        raise ValueError("click_direction must be either 'L' or 'R'.")

    n_locks = problem["locks"]

    direction_value = 1 if click_direction == "L" else -1

    movement = [0] * n_locks
    movement[selected_lock - 1] += direction_value

    deps = problem["dependencies"].get(str(selected_lock), [])

    for dep in deps:
        dep_lock = dep["lock"]
        dep_direction = dep["direction"]

        if dep_direction == "same":
            movement[dep_lock - 1] += direction_value
        elif dep_direction == "opposite":
            movement[dep_lock - 1] -= direction_value
        else:
            raise ValueError(f"Invalid dependency direction: {dep_direction}")

    new_position = [
        position[i] + movement[i]
        for i in range(n_locks)
    ]

    valid = all(
        problem["min_pos"] <= x <= problem["max_pos"]
        for x in new_position
    )

    return {
        "selected_lock": selected_lock,
        "click_direction": click_direction,
        "move": f"{selected_lock}{click_direction}",
        "before": position,
        "movement": movement,
        "after": new_position,
        "valid": valid
    }


def get_legal_moves(
    problem: Dict[str, Any],
    position: List[int]
) -> List[Dict[str, Any]]:

    legal_moves = []

    for lock in range(1, problem["locks"] + 1):
        for click_direction in ["L", "R"]:

            move = apply_lock_move(
                problem=problem,
                position=position,
                selected_lock=lock,
                click_direction=click_direction
            )

            if move["valid"]:
                legal_moves.append(move)

    return legal_moves


def validate_problem(problem: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    warnings = []

    start = problem["start"]
    target = problem["target"]
    n_locks = problem["locks"]
    min_pos = problem["min_pos"]
    max_pos = problem["max_pos"]
    dependencies = problem["dependencies"]

    if len(start) != n_locks:
        errors.append("The number of starting positions does not match the number of locks.")

    if any(x < min_pos or x > max_pos for x in start):
        errors.append("At least one starting position is outside the allowed range.")

    if target < min_pos or target > max_pos:
        errors.append("The target position is outside the allowed range.")

    expected_locks = {str(i) for i in range(1, n_locks + 1)}
    actual_locks = set(dependencies.keys())

    missing_locks = expected_locks - actual_locks
    extra_locks = actual_locks - expected_locks

    if missing_locks:
        warnings.append(
            "Missing dependency entries for locks: "
            + ", ".join(sorted(missing_locks, key=int))
        )

    if extra_locks:
        warnings.append(
            "Dependency entries contain locks outside the expected range: "
            + ", ".join(sorted(extra_locks))
        )

    for lock_id in expected_locks:
        deps = dependencies.get(lock_id, [])

        if not isinstance(deps, list):
            errors.append(f"Dependencies for lock {lock_id} must be a list.")
            continue

        for dep in deps:
            if "lock" not in dep:
                errors.append(f"Lock {lock_id} has a dependency without a lock field.")
                continue

            dep_lock = dep["lock"]

            if not isinstance(dep_lock, int):
                errors.append(f"Lock {lock_id} has a non-integer dependency lock.")
            elif dep_lock < 1 or dep_lock > n_locks:
                errors.append(f"Lock {lock_id} depends on an out-of-range lock: {dep_lock}")

            if "direction" not in dep:
                errors.append(f"Lock {lock_id} has a dependency without a direction field.")
                continue

            dep_direction = dep["direction"]

            if dep_direction not in ["same", "opposite"]:
                errors.append(
                    f"Lock {lock_id} has an invalid dependency direction: {dep_direction}"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def reconstruct_path(
    end_key: str,
    parent: Dict[str, Optional[str]],
    move_to_state: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:

    path = []
    current_key = end_key

    while parent[current_key] is not None:
        move_info = move_to_state[current_key].copy()
        path.append(move_info)
        current_key = parent[current_key]

    path.reverse()

    for i, step in enumerate(path, start=1):
        step["step"] = i

    return path


def check_lock_problem(
    problem: Dict[str, Any],
    max_states: int = 20000,
    show_closest: int = 20
) -> Dict[str, Any]:

    validation = validate_problem(problem)

    if not validation["valid"]:
        return {
            "valid_configuration": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "solved": None,
            "message": "Invalid puzzle configuration."
        }

    start = problem["start"]
    target_vec = [problem["target"]] * problem["locks"]

    start_key = state_key(start)
    target_key = state_key(target_vec)

    queue = deque([start])

    visited = {start_key}
    parent = {start_key: None}
    move_to_state = {}
    state_position = {start_key: start}

    found = False

    while queue:
        current = queue.popleft()
        current_key = state_key(current)

        if current_key == target_key:
            found = True
            break

        legal_moves = get_legal_moves(problem, current)

        for move in legal_moves:
            next_pos = move["after"]
            next_key = state_key(next_pos)

            if next_key not in visited:
                visited.add(next_key)
                parent[next_key] = current_key
                state_position[next_key] = next_pos

                move_to_state[next_key] = {
                    "selected_lock": move["selected_lock"],
                    "click_direction": move["click_direction"],
                    "move": move["move"],
                    "before": state_key(move["before"]),
                    "movement": state_key(move["movement"]),
                    "after": state_key(move["after"])
                }

                queue.append(next_pos)

        if len(visited) > max_states:
            raise RuntimeError("Maximum number of states exceeded. Increase max_states.")

    reachable_states = []

    for key, pos in state_position.items():
        distance = sum(abs(pos[i] - target_vec[i]) for i in range(problem["locks"]))
        max_single_lock_distance = max(abs(pos[i] - target_vec[i]) for i in range(problem["locks"]))

        reachable_states.append({
            "state": key,
            "position": pos,
            "distance": distance,
            "max_single_lock_distance": max_single_lock_distance
        })

    reachable_states.sort(
        key=lambda x: (x["distance"], x["max_single_lock_distance"])
    )

    if found:
        path = reconstruct_path(
            end_key=target_key,
            parent=parent,
            move_to_state=move_to_state
        )

        moves_short = ", ".join(step["move"] for step in path)

        return {
            "valid_configuration": True,
            "errors": [],
            "warnings": validation["warnings"],
            "solved": True,
            "message": "Puzzle solved.",
            "visited_states": len(visited),
            "steps": len(path),
            "path": path,
            "moves_short": moves_short,
            "reachable_states": reachable_states
        }

    closest_state = reachable_states[0]
    closest_path = reconstruct_path(
        end_key=closest_state["state"],
        parent=parent,
        move_to_state=move_to_state
    )

    closest_moves_short = ", ".join(step["move"] for step in closest_path)

    return {
        "valid_configuration": True,
        "errors": [],
        "warnings": validation["warnings"],
        "solved": False,
        "message": "No path to the target state was found.",
        "visited_states": len(visited),
        "closest_state": closest_state["state"],
        "closest_distance": closest_state["distance"],
        "closest_path": closest_path,
        "closest_moves_short": closest_moves_short,
        "closest_states": reachable_states[:show_closest],
        "reachable_states": reachable_states
    }


# ============================================================
# Streamlit UI
# ============================================================

st.set_page_config(
    page_title="Gothic Lock Solver",
    page_icon="🔐",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Left-align markdown and alert text */
    [data-testid="stMarkdownContainer"] {
        text-align: left;
    }

    /* Left-align Streamlit buttons */
    div[data-testid="stButton"] > button {
        text-align: left !important;
        justify-content: flex-start !important;
        align-items: center !important;
        white-space: normal !important;
        height: auto !important;
        padding-top: 0.75rem !important;
        padding-bottom: 0.75rem !important;
    }

    div[data-testid="stButton"] > button * {
        text-align: left !important;
        justify-content: flex-start !important;
    }

    div[data-testid="stButton"] p {
        text-align: left !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔐 Gothic Lock Solver — Direct Version")
st.caption("A small BFS solver for the Gothic Remake lock puzzle.")

st.markdown("## About this version")

st.info(
    """
    This is a shortened version of the original app, with direct access to the solver.

    I still encourage you to use the original version first. In that version, before reaching the 
    solver, you get an additional chance to stop and think about whether you really want to simplify 
    a challenge that you might still be able to solve by trying a little longer.

    The original goal of that version was to protect you from the impulsive desire to make the game 
    easier at the exact moment when the challenge becomes frustrating.

    However, after remembering that PC players can literally install mods that remove lockpicking 
    altogether, I realized that this app is simply one of many ways to adapt the gaming experience 
    to your own needs. It may also be especially useful for console players, who can open the app 
    on their phone while playing.

    So this is not meant as gamer elitism. Everyone can play however they want.
    """
)

st.subheader("1. Starting positions")
st.caption("Lock 1 is the one closest to the player.")

start_cols = st.columns(int(n_locks))
start = []

for i, col in enumerate(start_cols, start=1):
    with col:
        pos = st.number_input(
            f"Lock {i}",
            min_value=int(min_pos),
            max_value=int(max_pos),
            value=int(target),
            step=1,
            key=f"start_{i}"
        )
        start.append(int(pos))
        


st.subheader("2. Define lock dependencies")

st.write(
    "For each lock, mark what happens to the other locks when you click it. "
    "`Same` means the affected lock moves in the same physical direction. "
    "`Opposite` means it moves in the opposite physical direction."
)

dependencies = {str(i): [] for i in range(1, int(n_locks) + 1)}

for source_lock in range(1, int(n_locks) + 1):

    st.markdown(f"### Lock {source_lock}")

    target_locks = [
        lock for lock in range(1, int(n_locks) + 1)
        if lock != source_lock
    ]

    cols = st.columns(len(target_locks))

    for col, target_lock in zip(cols, target_locks):
        with col:
            dep = st.radio(
                label=f"Lock {target_lock}",
                options=["None", "Same", "Opposite"],
                index=0,
                horizontal=False,
                key=f"dep_{source_lock}_{target_lock}"
            )

            if dep == "Same":
                dependencies[str(source_lock)].append({
                    "lock": target_lock,
                    "direction": "same"
                })

            if dep == "Opposite":
                dependencies[str(source_lock)].append({
                    "lock": target_lock,
                    "direction": "opposite"
                })

    st.divider()

problem = {
    "start": start,
    "target": int(target),
    "locks": int(n_locks),
    "min_pos": int(min_pos),
    "max_pos": int(max_pos),
    "dependencies": dependencies
}


st.subheader("3. Get solution")

col_solve, col_json = st.columns([1, 1])

with col_solve:
    solve_button = st.button("Solve puzzle", type="primary", use_container_width=True)

with col_json:
    show_json = st.checkbox("Show generated JSON")


def show_move_sequence(moves: str) -> None:
    st.markdown(
        f"""
        <div style="
            font-size: 1.1rem;
            line-height: 1.6;
            padding: 0.75rem 1rem;
            border: 1px solid #ddd;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            word-wrap: break-word;
            overflow-wrap: break-word;
        ">
            {moves}
        </div>
        """,
        unsafe_allow_html=True
    )


if show_json:
    config_preview = {
        "start": problem["start"],
        "target": problem["target"],
        "locks": problem["locks"],
        "positions": [problem["min_pos"], problem["max_pos"]],
        "dependencies": problem["dependencies"]
    }

    st.code(
        json.dumps(config_preview, indent=2),
        language="json"
    )


if solve_button:

    try:
        result = check_lock_problem(
            problem=problem,
            max_states=int(max_states),
            show_closest=20
        )

        if result["warnings"]:
            for warning in result["warnings"]:
                st.warning(warning)

        if result["errors"]:
            for error in result["errors"]:
                st.error(error)

        if result["solved"] is True:

            if result["steps"] == 0:
                st.warning(
                    "All locks are currently set to 4, which means the chest is already solved. "
                    "If this was not intended, please enter the actual starting positions of the locks first."
                )

            else:
                st.success(f"Puzzle solved in {result['steps']} steps.")

                st.markdown("### Short move sequence")
                show_move_sequence(result["moves_short"])

                st.markdown("### Full path")
                path_df = pd.DataFrame(result["path"])

                if not path_df.empty:
                    path_df = path_df[
                        [
                            "step",
                            "move",
                            "before",
                            "movement",
                            "after",
                            "selected_lock",
                            "click_direction"
                        ]
                    ]

                    st.dataframe(
                        path_df,
                        use_container_width=True,
                        hide_index=True
                    )

                st.caption(f"Visited states: {result['visited_states']}")

        elif result["solved"] is False:
            st.error(
                "No solution found with the current configuration. "
                "Please make sure that all lock positions and dependencies were entered correctly."
            )

            st.write(f"Visited states: `{result['visited_states']}`")
            st.write(f"Closest reachable state: `{result['closest_state']}`")
            st.write(f"Closest distance: `{result['closest_distance']}`")

            st.markdown("### Closest move sequence")
            show_move_sequence(result["closest_moves_short"])

            st.markdown("### Closest reachable states")
            closest_df = pd.DataFrame(result["closest_states"])

            st.dataframe(
                closest_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.error(result["message"])

    except Exception as e:
        st.exception(e)
