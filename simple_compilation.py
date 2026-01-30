# simple_compilation.py
from __future__ import absolute_import, division, print_function

import os
import os.path as op
import shlex

from fable.compat import (
    repo_root,
    full_command_path,
    get_gcc_version,
    easy_run,
    Sorry,
)


def _split_flags(s):
    if s is None:
        return []
    s = str(s).strip()
    if not s:
        return []
    return shlex.split(s)


def _split_paths(s):
    if s is None:
        return []
    s = str(s).strip()
    if not s:
        return []
    return [p for p in s.split(":") if p]


class environment(object):
    """
    Standalone compilation environment (no libtbx).

    Environment variables for MPLAPACK integration:
      - FABLE_CXX / FABLE_COMPILER: C++ compiler (default: g++)
      - FABLE_CXXSTD: C++ standard (default: c++11)
      - FABLE_CPPFLAGS: preprocessor flags
      - FABLE_CXXFLAGS: compiler flags
      - FABLE_INCLUDE_DIRS: colon-separated include dirs
      - FABLE_LDFLAGS: linker flags
      - FABLE_LIB_DIRS: colon-separated library dirs
      - FABLE_LIBS: extra libs/flags (string appended as-is)
      - FABLE_BUILD_DIR: build directory (optional; default: <repo_root>/build)
    """

    def __init__(self, compiler=None):
        self.fable_dist = str(repo_root())
        self.build_dir = os.environ.get(
            "FABLE_BUILD_DIR", op.join(self.fable_dist, "build"))
        os.makedirs(self.build_dir, exist_ok=True)

        self.compiler = (
            compiler
            or os.environ.get("FABLE_CXX")
            or os.environ.get("FABLE_COMPILER")
            or "g++"
        )
        self.compiler_path = full_command_path(self.compiler)
        self.gcc_version = get_gcc_version(self.compiler)

        self.exe_suffix = ".exe" if os.name == "nt" else ""
        self.have_pch = False

        self.cxxstd = os.environ.get("FABLE_CXXSTD", "c++11")
        self.cppflags = _split_flags(os.environ.get("FABLE_CPPFLAGS", ""))
        self.cxxflags = _split_flags(os.environ.get("FABLE_CXXFLAGS", ""))
        self.ldflags = _split_flags(os.environ.get("FABLE_LDFLAGS", ""))

        include_dirs = [self.fable_dist]
        include_dirs += _split_paths(os.environ.get("FABLE_INCLUDE_DIRS", ""))
        self.include_dirs = include_dirs

        lib_dirs = _split_paths(os.environ.get("FABLE_LIB_DIRS", ""))
        self.lib_dirs = lib_dirs

        # Kept as a raw string so users can pass complex flags easily.
        self.libs = os.environ.get("FABLE_LIBS", "").strip()

    def set_have_pch(self):
        self.have_pch = True

    def _mk_cmd(self, args):
        return " ".join(shlex.quote(a) for a in args)

    def _common_flags(self, disable_warnings=False):
        """Build common compiler flags used for both compilation and linking."""
        include_flags = []
        for d in self.include_dirs:
            include_flags += ["-I", d]

        common_flags = []
        common_flags += ["-std=%s" % self.cxxstd]
        common_flags += include_flags
        common_flags += self.cppflags
        common_flags += self.cxxflags
        if disable_warnings:
            common_flags += ["-w"]
        return common_flags

    def _libdir_flags(self):
        """Build library directory flags."""
        libdir_flags = []
        for d in self.lib_dirs:
            libdir_flags += ["-L", d]
        return libdir_flags

    def file_name_obj(self, file_name_cpp):
        root, _ = os.path.splitext(file_name_cpp)
        return root + (".obj" if os.name == "nt" else ".o")

    def file_name_exe(self, exe_root):
        """Generate executable file name from root name."""
        return exe_root + self.exe_suffix

    def compilation_command(self, file_name_cpp, disable_warnings=False):
        """Generate compilation command string for a C++ source file.

        Args:
            file_name_cpp: Path to C++ source file
            disable_warnings: If True, suppress warnings

        Returns:
            Complete compilation command string
        """
        if self.compiler_path is None:
            raise RuntimeError(
                "C++ compiler not available: %s" % self.compiler)

        obj = self.file_name_obj(file_name_cpp)
        common_flags = self._common_flags(disable_warnings=disable_warnings)
        cmd = [self.compiler_path] + common_flags + \
            ["-c", file_name_cpp, "-o", obj]
        return self._mk_cmd(cmd)

    def link_command(self, file_names_obj, exe_root):
        """Generate link command string for object files.

        Args:
            file_names_obj: List of object file paths
            exe_root: Base name for output executable

        Returns:
            Complete link command string
        """
        if self.compiler_path is None:
            raise RuntimeError(
                "C++ compiler not available: %s" % self.compiler)

        exe = self.file_name_exe(exe_root)
        libdir_flags = self._libdir_flags()
        cmd = [self.compiler_path] + file_names_obj + \
            ["-o", exe] + libdir_flags + self.ldflags
        if self.libs:
            cmd += _split_flags(self.libs)
        return self._mk_cmd(cmd)

    def build(
        self,
        exe_name=None,
        link=True,
        file_name_cpp=None,
        show_command=False,
        disable_warnings=False,
        Error=RuntimeError,
        pch_name=None,
    ):
        if file_name_cpp is None:
            raise Error("file_name_cpp is required")
        if self.compiler_path is None:
            raise Error("C++ compiler not available: %s" % self.compiler)

        file_name_cpp = str(file_name_cpp)

        common_flags = self._common_flags(disable_warnings=disable_warnings)
        libdir_flags = self._libdir_flags()

        # Precompiled header build (optional)
        if pch_name is not None:
            # GCC uses <header>.gch next to the header.
            out_pch = file_name_cpp + ".gch"
            cmd = [self.compiler_path] + common_flags + \
                ["-x", "c++-header", file_name_cpp, "-o", out_pch]
            cmd_str = self._mk_cmd(cmd)
            if show_command:
                print(cmd_str)
            buffers = easy_run.fully_buffered(command=cmd_str)
            buffers.raise_if_errors_or_output(Error=Error)
            return out_pch

        if link:
            out = exe_name
            if out is None:
                base = op.splitext(op.basename(file_name_cpp))[0]
                out = base + self.exe_suffix
            cmd = [self.compiler_path] + common_flags + \
                [file_name_cpp, "-o", out] + libdir_flags + self.ldflags
            if self.libs:
                cmd += _split_flags(self.libs)
            cmd_str = self._mk_cmd(cmd)
            if show_command:
                print(cmd_str)
            buffers = easy_run.fully_buffered(command=cmd_str)
            buffers.raise_if_errors_or_output(Error=Error)
            return out

        # Compile only -> object file
        base = exe_name
        if base is None:
            base = op.splitext(op.basename(file_name_cpp))[0]
        obj = op.splitext(base)[0] + ".o"
        cmd = [self.compiler_path] + common_flags + \
            ["-c", file_name_cpp, "-o", obj]
        cmd_str = self._mk_cmd(cmd)
        if show_command:
            print(cmd_str)
        buffers = easy_run.fully_buffered(command=cmd_str)
        buffers.raise_if_errors_or_output(Error=Error)
        return obj
