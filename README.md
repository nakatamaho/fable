# Fable a Fortran-to-C++ translator (a fork)

This repository is a fork of **Fable**, a Fortran-to-C++ translator.
It includes a small wrapper script `fable.cout` to run the local checkout
reliably (without depending on a separately-installed `fable`/`fable_org`).

## Requirements

- Python 3.x
- A POSIX shell (`bash`)

## Checkout (clone) this fork

Pick any directory you like for the checkout.

```bash
# Example:
mkdir -p ~/src
cd ~/src

# Clone your fork (replace with your actual fork URL)
git clone <YOUR_FORK_URL> fable
cd fable
````

Switch to a specific branch/tag if needed:

```bash
git fetch --all --tags
git checkout <branch-or-tag>
```

## Quick start: run `cout` via the wrapper

From inside the checkout:

```bash
# Make sure it is executable (only once)
chmod +x ./fable.cout

# Translate a Fortran file
./fable.cout path/to/input.f > output.cpp
```

You can also invoke it explicitly via `bash`:

```bash
bash ~/src/fable/fable.cout path/to/input.f > output.cpp
```

Any extra arguments after the input file are passed through to `cout`:

```bash
./fable.cout path/to/input.f -- --help
```

## Run from another repository (e.g., MPLAPACK)

You do **not** need to `cd` into this repo.
Just call the wrapper by absolute path:

```bash
bash ~/<checkoutdir>/fable.cout /path/to/fortran/source.f > /tmp/out.cpp
```

Because the wrapper resolves imports relative to its own location, it will
always use the `fable` package from this checkout.

## Environment variables

* `PYTHON`
  Select the Python interpreter to use.

  ```bash
  PYTHON=python3.11 bash ~/<checkoutdir>/fable.cout input.f > out.cpp
  ```

* `FABLE_ROOT` (optional)
  Override the `fable` package root directory (where `__init__.py` exists).
  Normally you do not need this.

## Troubleshooting

* `ModuleNotFoundError: fable...`
  Ensure you are using the wrapper script from this checkout and that the
  directory contains `__init__.py` at the repository root.

* Script says "not inside a git repository"
  This fork’s wrapper does not require a git toplevel lookup. If you see
  that error, you are likely running an older wrapper. Update `fable.cout`
  to the version in this fork.

