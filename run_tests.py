from __future__ import absolute_import, division, print_function
import subprocess
import os
from fable.compat import repo_root

import sys
from pathlib import Path

# Make 'import fable.*' work even when running this script from inside
# the package directory (e.g. /path/to/fable/run_tests.py).
_this_file = Path(__file__).resolve()
_pkg_dir = _this_file.parent          # .../fable
_pkg_parent = str(_pkg_dir.parent)    # .../
if _pkg_parent not in sys.path:
    sys.path.insert(0, _pkg_parent)


# Ensure 'fable' is importable when running this script directly from a checkout.
_repo_root = Path(__file__).resolve().parent
_repo_parent = str(_repo_root.parent)
if _repo_parent not in sys.path:
    sys.path.insert(0, _repo_parent)


tst_list = (
    "$D/tst_ext.py",
    "$D/tst_equivalence.py",
    "$D/tst_read.py",
    "$D/tst_cout.py",
    "$D/test/tst_show_calls.py",
    "$D/test/tst_command_line.py",
    "$D/test/tst_separate_files.py",
    ["$D/tst_cout_compile.py", "stop"],
)

tst_list_expected_unstable = [
    "$D/test/tst_io.py",
]


def _expand_macros(path, dist_dir, build_dir):
    # Support the same $D macro as libtbx.test_utils.run_tests.
    # $B is added for convenience.
    return path.replace("$D", dist_dir).replace("$B", build_dir)


def _env_for_child_processes(dist_dir, build_dir):
    env = os.environ.copy()
    env.setdefault("FABLE_ROOT", dist_dir)
    env.setdefault("FABLE_BUILD_DIR", build_dir)

    # Ensure the package import works in child processes too.
    old = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = _repo_parent if not old else f"{_repo_parent}:{old}"
    return env


def run(include_unstable=False):
    dist_dir = str(repo_root())

    build_dir = os.environ.get(
        "FABLE_BUILD_DIR", os.path.join(dist_dir, "build"))
    os.makedirs(build_dir, exist_ok=True)

    env = _env_for_child_processes(dist_dir, build_dir)
    cwd = dist_dir

    tests = list(tst_list)
    if include_unstable:
        tests += list(tst_list_expected_unstable)

    for entry in tests:
        stop_on_fail = False
        if isinstance(entry, (list, tuple)):
            test_path = entry[0]
            stop_on_fail = "stop" in entry[1:]
        else:
            test_path = entry

        test_path = _expand_macros(test_path, dist_dir, build_dir)
        if not os.path.isabs(test_path):
            test_path = os.path.join(dist_dir, test_path)

        cmd = [sys.executable, test_path]
        print("==>", " ".join(cmd))
        r = subprocess.run(cmd, cwd=cwd, env=env)
        if r.returncode != 0:
            print(f"FAILED: {test_path} (exit={r.returncode})",
                  file=sys.stderr)
            if stop_on_fail:
                return r.returncode

    return 0


if (__name__ == "__main__"):
    run()
    include_unstable = "--unstable" in sys.argv[1:]
    sys.exit(run(include_unstable=include_unstable))
