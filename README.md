# Fable: a Fortran-to-C++ translator (fork)

This repository is a fork of **Fable**, a Fortran-to-C++ translator.
It includes a small wrapper script `fable.cout` to run the local checkout
reliably (without depending on a separately-installed `fable`/`fable_org`).

## Upstream (original project)

- https://cci.lbl.gov/fable/

## Citation

If you use FABLE in academic work, please cite:

Grosse-Kunstleve RW, Terwilliger TC, Sauter NK, Adams PD.
Automatic Fortran to C++ conversion with FABLE.
*Source Code for Biology and Medicine.* 2012;7:5.
DOI: 10.1186/1751-0473-7-5

Links:

- DOI: https://doi.org/10.1186/1751-0473-7-5
- Publisher page: https://link.springer.com/article/10.1186/1751-0473-7-5
- PubMed: https://pubmed.ncbi.nlm.nih.gov/22640868/
- PMC (full text): https://pmc.ncbi.nlm.nih.gov/articles/PMC3448510/

## Requirements

- Python 3.x
- A POSIX shell (`bash`)

## Checkout (clone) this fork

Pick any directory you like for the checkout.

```bash
# Example:
mkdir -p ~/src
cd ~/src

# Clone the repository
git clone https://github.com/nakatamaho/fable.git fable
cd fable
````

## Quick start: run `cout` via the wrapper

From inside the checkout:

```bash
# Make sure it is executable (only once)
chmod +x ./fable.cout

# Translate a Fortran file
$ ./fable.cout test/valid/data_01.f
#include <fem.hpp> // Fortran EMulation library of fable module

namespace placeholder_please_replace {

using namespace fem::major_types;

struct common :
  fem::common
{
  fem::cmn_sve program_prog_sve;

  common(
    int argc,
    char const* argv[])
  :
    fem::common(argc, argv)
  {}
};

struct program_prog_save
{
  int num;

  program_prog_save() :
    num(fem::int0)
  {}
};

void
program_prog(
  int argc,
  char const* argv[])
{
  common cmn(argc, argv);
  FEM_CMN_SVE(program_prog);
  common_write write(cmn);
  // SAVE
  int& num = sve.num;
  //
  if (is_called_first_time) {
    num = 3;
  }
  write(6, star), num;
}

} // namespace placeholder_please_replace

int
main(
  int argc,
  char const* argv[])
{
  return fem::main_with_catch(
    argc, argv,
    placeholder_please_replace::program_prog);

}
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
  This fork's wrapper does not require a git toplevel lookup. If you see
  that error, you are likely running an older wrapper. Update `fable.cout`
  to the version in this fork.

