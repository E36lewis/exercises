"""
check_exercises.py

Compares exercise names in exercise_list.txt against video files in the exercises folder.
Reports mismatches in both directions.

Usage:
    python check_exercises.py
    python check_exercises.py --txt path/to/exercise_list.txt --folder path/to/exercises
"""

import ast
import os
import re
import argparse


def load_exercise_list(txt_path: str) -> list[tuple[str, str]]:
    """Parse exercise_list.txt and return a list of (tool, exercise_name) tuples."""
    with open(txt_path, "r") as f:
        content = f.read().strip()
    exercises = ast.literal_eval(content)
    return [(tool.strip().lower(), name.strip().lower()) for tool, name in exercises]


def get_folder_exercises(exercises_dir: str) -> dict[str, set[str]]:
    """
    Scan the exercises folder and return a dict:
        { tool_folder_name: set of exercise_names }

    Filename format assumed: {gender_prefix}_{exercise_name}_{frame}.mp4
    e.g. f_bench_press_60.mp4 -> exercise: "bench press", tool: "barbell"

    Gender prefix: single letter (f_ or m_)
    Frame suffix:  trailing _<digits>
    """
    folder_map: dict[str, set[str]] = {}

    for tool_folder in os.listdir(exercises_dir):
        tool_path = os.path.join(exercises_dir, tool_folder)
        if not os.path.isdir(tool_path):
            continue

        tool_key = tool_folder.strip().lower().replace("_", " ")
        exercise_names: set[str] = set()

        for filename in os.listdir(tool_path):
            if not filename.lower().endswith(".mp4"):
                continue

            stem = os.path.splitext(filename)[0]  # remove .mp4

            # Strip leading gender prefix: one or two letters followed by underscore
            stem = re.sub(r"^[a-z]{1,2}_", "", stem)

            # Strip trailing frame number: _<digits> at the end
            stem = re.sub(r"_\d+$", "", stem)

            # Convert underscores to spaces
            exercise_name = stem.replace("_", " ").strip().lower()
            exercise_names.add(exercise_name)

        folder_map[tool_key] = exercise_names

    return folder_map


def normalize_tool(tool: str) -> str:
    """Normalize tool names to match folder naming conventions."""
    return tool.replace("_", " ").strip().lower()


def check(txt_path: str, exercises_dir: str):
    print(f"\n{'='*60}")
    print(f"  Exercise List:    {txt_path}")
    print(f"  Exercises Folder: {exercises_dir}")
    print(f"{'='*60}\n")

    txt_exercises = load_exercise_list(txt_path)
    folder_exercises = get_folder_exercises(exercises_dir)

    # ── 1. Names in txt with no matching video file ──────────────────────────
    missing_files: list[tuple[str, str]] = []
    for tool, name in txt_exercises:
        tool_norm = normalize_tool(tool)
        folder_names = folder_exercises.get(tool_norm, set())
        if name not in folder_names:
            missing_files.append((tool, name))

    # ── 2. Video files with no matching entry in txt ─────────────────────────
    txt_set: dict[str, set[str]] = {}
    for tool, name in txt_exercises:
        txt_set.setdefault(normalize_tool(tool), set()).add(name)

    extra_files: list[tuple[str, str]] = []
    for tool_folder, names in folder_exercises.items():
        txt_names = txt_set.get(tool_folder, set())
        for name in names:
            if name not in txt_names:
                extra_files.append((tool_folder, name))

    # ── Report ───────────────────────────────────────────────────────────────
    if missing_files:
        print(f"❌  In txt but NO matching video file ({len(missing_files)}):")
        for tool, name in sorted(missing_files):
            print(f"    [{tool}]  {name}")
    else:
        print("✅  All txt entries have a matching video file.")

    print()

    if extra_files:
        print(f"⚠️   Video files with NO matching txt entry ({len(extra_files)}):")
        for tool, name in sorted(extra_files):
            print(f"    [{tool}]  {name}")
    else:
        print("✅  All video files have a matching txt entry.")

    print()


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description="Check exercise names vs video files.")
    parser.add_argument(
        "--txt",
        default=os.path.join(script_dir, "exercise_list.txt"),
        help="Path to exercise_list.txt",
    )
    parser.add_argument(
        "--folder",
        default=os.path.join(script_dir, "exercises"),
        help="Path to the exercises folder",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.txt):
        print(f"ERROR: txt file not found: {args.txt}")
        exit(1)
    if not os.path.isdir(args.folder):
        print(f"ERROR: exercises folder not found: {args.folder}")
        exit(1)

    check(args.txt, args.folder)