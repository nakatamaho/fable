# compat.py
from __future__ import annotations

import atexit
import difflib
import math
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Union


def to_bytes(value, codec="utf-8", errors="strict", encoding=None):
    """Convert str/bytes-like to bytes.

    - Accepts 'codec' (preferred) and also 'encoding' as an alias.
    - Returns bytes unchanged.
    - Raises TypeError for unsupported types.
    """
    if encoding is not None:
        # Keep behavior deterministic if both are provided
        if codec != "utf-8" and codec != encoding:
            raise TypeError("to_bytes: specify only one of 'codec' or 'encoding'")
        codec = encoding

    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, str):
        return value.encode(codec, errors)

    raise TypeError(
        f"to_bytes must receive a str, bytes, bytearray, or memoryview object, got {type(value).__name__}"
    )

# -----------------------------------------------------------------------------
# Paths / environment
# -----------------------------------------------------------------------------


def repo_root() -> Path:
    # Allow overriding the root for MPLAPACK integration.
    # FABLE_ROOT should point to the directory containing __init__.py.
    env = os.environ.get("FABLE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent


def dist_path(*parts: str) -> str:
    return str(repo_root().joinpath(*parts))


def under_dist(module_name: str = "fable", path: str = "", test: Optional[Callable[[str], bool]] = None) -> str:
    # Keep signature similar to libtbx.env.under_dist but do not depend on libtbx.
    p = dist_path(path) if path else str(repo_root())
    if test is not None and not test(p):
        raise FileNotFoundError(p)
    return p


def show_string(value: object) -> str:
    return repr(value)


# -----------------------------------------------------------------------------
# Small utilities (runtime)
# -----------------------------------------------------------------------------

class Sorry(RuntimeError):
    pass


def to_bytes(value: Union[str, bytes], encoding: str = "utf-8") -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode(encoding, errors="strict")
    return bytes(value)


def remove_files(*paths: Union[str, Sequence[str]]) -> None:
    flat: List[str] = []
    for p in paths:
        if p is None:
            continue
        if isinstance(p, (list, tuple)):
            flat.extend([str(x) for x in p])
        else:
            flat.append(str(p))
    for p in flat:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass


def full_command_path(command: str) -> Optional[str]:
    return shutil.which(command)


def get_gcc_version(command_name: str = "g++") -> Optional[int]:
    # Return gcc version as MAJOR*10000 + MINOR*100 + PATCH (like libtbx.env_config).
    exe = shutil.which(command_name)
    if exe is None:
        return None
    for args in ([exe, "-dumpfullversion", "-dumpversion"], [exe, "-dumpversion"]):
        try:
            out = subprocess.check_output(args, text=True).strip()
        except Exception:
            continue
        if not out:
            continue
        parts = out.split(".")
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return major * 10000 + minor * 100 + patch
        except Exception:
            continue
    return None


def iround(x: float) -> int:
    # Round half away from zero (matches classic libtbx behavior).
    if x < 0:
        return int(x - 0.5)
    return int(x + 0.5)


def iceil(x: float) -> int:
    return iround(math.ceil(x))


def product(seq: Iterable[int]) -> Optional[int]:
    result: Optional[int] = None
    for v in seq:
        result = v if result is None else result * v
    return result


class _AutoType:
    def __repr__(self) -> str:
        return "Auto"


Auto = _AutoType()


class group_args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        args = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"group_args({args})"


class mutable:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        args = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"mutable({args})"


class dict_with_default_0(dict):
    def __missing__(self, key):
        return 0


# -----------------------------------------------------------------------------
# Topological sort (runtime)
# -----------------------------------------------------------------------------

class _TopoSort:
    def stable(self, connections: Iterable[Tuple[str, Iterable[str]]]) -> List[str]:
        rank = {}
        deps_by_node = {}
        for node, deps in connections:
            if node not in rank:
                rank[node] = len(rank)
            deps = list(deps)
            deps_by_node[node] = deps
            for d in deps:
                if d not in rank:
                    rank[d] = len(rank)

        succs = {n: set() for n in rank}
        indeg = {n: 0 for n in rank}
        for node, deps in deps_by_node.items():
            for d in deps:
                succs.setdefault(d, set()).add(node)
                indeg[node] += 1

        ready = [n for n, deg in indeg.items() if deg == 0]
        ready.sort(key=lambda n: rank[n])

        result = []
        while ready:
            n = ready.pop(0)
            result.append(n)
            for s in succs.get(n, ()):
                indeg[s] -= 1
                if indeg[s] == 0:
                    ready.append(s)
                    ready.sort(key=lambda x: rank[x])
        return result

    def strongly_connected_components(
        self,
        successors_by_node: dict,
        omit_single_node_components: bool = True,
    ) -> List[Tuple[str, ...]]:
        index = {}
        lowlink = {}
        stack = []
        on_stack = set()
        result = []
        counter = [0]

        def visit(node):
            if node in index:
                return
            idx = counter[0]
            counter[0] += 1
            index[node] = lowlink[node] = idx
            stack.append(node)
            on_stack.add(node)
            for succ in successors_by_node.get(node, ()):
                if succ not in index:
                    visit(succ)
                    lowlink[node] = min(lowlink[node], lowlink[succ])
                elif succ in on_stack:
                    lowlink[node] = min(lowlink[node], index[succ])
            if lowlink[node] == idx:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    comp.append(w)
                    if w == node:
                        break
                if (not omit_single_node_components) or len(comp) > 1:
                    result.append(tuple(comp))

        for node in successors_by_node:
            visit(node)
        return result


topological_sort = _TopoSort()


# -----------------------------------------------------------------------------
# Formatting helper (runtime)
# -----------------------------------------------------------------------------

def expandtabs_track_columns(s: str, tabsize: int = 8) -> Tuple[str, List[int]]:
    col = 0
    out: List[str] = []
    js: List[int] = []
    for ch in s:
        js.append(col)
        if ch == "\t":
            n = tabsize - (col % tabsize)
            out.append(" " * n)
            col += n
        else:
            out.append(ch)
            col += 1
    js.append(col)
    return "".join(out), js


# -----------------------------------------------------------------------------
# Subprocess helpers (used by compilation / tests)
# -----------------------------------------------------------------------------

@dataclass
class _Buffers:
    stdout_lines: List[str]
    stderr_lines: List[str]
    return_code: int

    def raise_if_errors(self, Error=RuntimeError) -> None:
        if self.return_code != 0:
            raise Error("\n".join(self.stderr_lines).strip())

    def raise_if_errors_or_output(self, Error=RuntimeError) -> None:
        if self.return_code != 0 or (len(self.stderr_lines) != 0 and any(self.stderr_lines)):
            raise Error("\n".join(self.stderr_lines).strip())


def fully_buffered(
    command: str,
    stdin_lines: Optional[Sequence[str]] = None,
    join_stdout_stderr: bool = False,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> _Buffers:
    if stdin_lines is None:
        stdin_text = None
    else:
        stdin_text = "\n".join(stdin_lines) + "\n"

    stderr_opt = subprocess.STDOUT if join_stdout_stderr else subprocess.PIPE
    p = subprocess.run(
        command,
        input=stdin_text,
        text=True,
        shell=True,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=stderr_opt,
    )
    out = p.stdout.splitlines()
    if join_stdout_stderr:
        err = []
    else:
        err = (p.stderr or "").splitlines()
    return _Buffers(stdout_lines=out, stderr_lines=err, return_code=p.returncode)


class easy_run:
    # Compatibility wrapper: keep a familiar call site style.
    @staticmethod
    def fully_buffered(**kwargs) -> _Buffers:
        return fully_buffered(**kwargs)

    @staticmethod
    def call(command: str, cwd: Optional[str] = None) -> None:
        subprocess.check_call(command, shell=True, cwd=cwd)


def show_times_at_exit(label: str = "Total time", out=None) -> None:
    start = time.time()
    if out is None:
        out = sys.stderr

    def _report():
        dt = time.time() - start
        print(f"{label}: {dt:.2f}s", file=out)

    atexit.register(_report)


# -----------------------------------------------------------------------------
# Test helpers
# -----------------------------------------------------------------------------

class Exception_expected(Exception):
    pass


def random_permutation_in_place(list: list) -> None:
    random.shuffle(list)


def approx_equal(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps * max(1.0, abs(a), abs(b))


def show_diff(actual, expected, fromfile: str = "actual", tofile: str = "expected") -> str:
    if isinstance(actual, (list, tuple)):
        actual = "".join(actual)
    else:
        actual = str(actual)
    if isinstance(expected, (list, tuple)):
        expected = "".join(expected)
    else:
        expected = str(expected)
    if actual == expected:
        return ""
    return "".join(difflib.unified_diff(
        actual.splitlines(True),
        expected.splitlines(True),
        fromfile=fromfile,
        tofile=tofile,
    ))


def anchored_block_show_diff(actual, offset: int, expected, fromfile: str = "actual", tofile: str = "expected") -> str:
    if isinstance(actual, (list, tuple)):
        a = "".join(actual)
    else:
        a = str(actual)
    if isinstance(expected, (list, tuple)):
        e = "".join(expected)
    else:
        e = str(expected)
    a_lines = a.splitlines(True)
    e_lines = e.splitlines(True)
    n = len(a_lines)
    start = offset if offset >= 0 else n + offset
    if start < 0:
        start = 0
    end = start + len(e_lines)
    a_block = "".join(a_lines[start:end])
    return show_diff(a_block, e, fromfile=fromfile, tofile=tofile)
