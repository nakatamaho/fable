from __future__ import absolute_import, division, print_function

import os
import sys


def _add_repo_root_to_sys_path():
    """Make the repository root importable.

    This test is often executed as a script:
      $ python test/tst_command_line.py

    In that mode, sys.path[0] is the test directory, so modules living at
    the repo root (e.g. compat.py) are not importable unless we add it.
    """
    this_dir = os.path.abspath(os.path.dirname(__file__))
    repo_root = os.path.abspath(os.path.join(this_dir, os.pardir))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    _prepend_repo_bin_to_path(repo_root)


def _prepend_repo_bin_to_path(repo_root):
    """Prepend <repo_root>/bin to PATH so 'fable.*' wrappers are found."""
    bin_dir = os.path.join(repo_root, "bin")
    if not os.path.isdir(bin_dir):
        return
    path = os.environ.get("PATH", "")
    parts = path.split(os.pathsep) if path else []
    if parts and parts[0] == bin_dir:
        return
    # Avoid duplicates while keeping precedence.
    if bin_dir in parts:
        parts = [p for p in parts if p != bin_dir]
    os.environ["PATH"] = os.pathsep.join([bin_dir] + parts)


def run(args):
    assert len(args) == 0
    _add_repo_root_to_sys_path()
    try:
        from compat import easy_run
    except ImportError:
        # If compat.py lives inside the fable package.
        from fable.compat import easy_run
    op = os.path
    t_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "valid")
    assert op.isdir(t_dir), t_dir

    assert t_dir.find('"') < 0
    n_errors = 0
    for command, expected_output_fragment in [
        ('fable.split "%ssubroutine_1.f"', 'program_prog.f'),
        ('fable.read --each "%swrite_star.f"', 'Success: 1'),
        ('fable.read --warnings "%sequivalence_mixed.f"',
            'Warning: EQUIVALENCE cluster with mixed data types: integer, real:'),
        ('fable.show_calls --write-graphviz-dot=tmp.dot'
            ' --top-procedure=sub "%sexternal_arg_layers.f"',
         'exch->exch_imp'),
        ('fable.show_calls "%sdependency_cycle.f"', 'sub1 sub2'),
        ('fable.fem_include_search_paths --with-quotes', 'fable'),
        ('fable.cout --each "%swrite_star.f"', 'return fem::main_with_catch'),
        ('fable.cout "%scommon_variants.f"',
            'Writing file: "fable_cout_common_report"'),
        ('fable.cout "%ssubroutine_3.f" --top-procedure=sub3'
         ' --fortran-file-comments',
            'nums(i) = i * 20;'),
        ('fable.cout --compile "%swrite_star.f"',
            'placeholder_please_replace::program_prog);'),
        ('fable.cout --namespace=test --run "%swrite_star.f"',
            'test::program_prog);'),
        ('fable.cout --example', '  -3   1  -5'),
        ('fable.cout %ssf.f --namespace example --run', '  -3   1  -5'),
        ('fable.cout "%sdynamic_parameters_1.f"'
            ' --dynamic-parameter="int root_size=1"',
         "const int root_size = cmn.dynamic_params.root_size;")]:
        if (expected_output_fragment.find("fable_cout_common_report") >= 0):
            join_stdout_stderr = True
        else:
            join_stdout_stderr = False
        if (command.find("%s") >= 0):
            command = command % (t_dir + os.sep)
        print(command)
        run_buffers = easy_run.fully_buffered(
            command=command,
            join_stdout_stderr=join_stdout_stderr)

        class SpecificError(RuntimeError):
            pass
        try:
            if (not join_stdout_stderr):
                run_buffers.raise_if_errors(Error=SpecificError)
        except SpecificError as e:
            n_errors += 1
            print("ERROR:")
            print(str(e))
            print()
        else:
            stdout_buffer = "\n".join(run_buffers.stdout_lines)
            if (expected_output_fragment is None):
                if (len(stdout_buffer) != 0):
                    n_errors += 1
                    print(stdout_buffer)
                    print("ERROR: unexpected output above.")
                    print()
            elif (stdout_buffer.find(expected_output_fragment) < 0):
                n_errors += 1
                print(stdout_buffer)
                print("ERROR: not found in output above:")
                print([expected_output_fragment])
                print()
    if (n_errors != 0):
        print("Number of errors:", n_errors)
        print("Done.")
    else:
        print("OK")


if (__name__ == "__main__"):
    import sys
    run(args=sys.argv[1:])
