# WORKSPACE.bazel Debugging Notes

This document captures the errors encountered when running `bazel build //...` against the initial `WORKSPACE.bazel` and how each was resolved.

---

## Error 1: Invalid label path in `load()`

**Error message:**
```
ERROR: Label '@@rules_python//python/pip.bzl:pip.bzl' is invalid because
'python/pip.bzl' is not a package; perhaps you meant to put the colon here:
'@@rules_python//python:pip.bzl/pip.bzl'?
```

**Cause:**
Bazel label syntax uses `//package:file`, not `//package/file`. The original load statement used a `/` to separate the package path from the `.bzl` filename:

```python
# Wrong
load("@rules_python//python/pip.bzl", "pip_parse")
```

**Fix:**
Replace the `/` before `pip.bzl` with `:`:

```python
# Correct
load("@rules_python//python:pip.bzl", "pip_parse")
```

---

## Error 2: `interpreter` no longer exported by `@python3//:defs.bzl`

**Error message:**
```
ERROR: file '@python3//:defs.bzl' does not contain symbol 'interpreter'
```

**Cause:**
The original WORKSPACE used a pattern from older versions of `rules_python` (0.x) where `python_register_toolchains` generated a `defs.bzl` that exported an `interpreter` label:

```python
load("@python3//:defs.bzl", "interpreter")

pip_parse(
    name = "python_deps",
    python_interpreter_target = interpreter,
    requirements_lock = "//:requirements.txt",
)
```

In `rules_python` 1.x, `defs.bzl` was restructured and no longer exports `interpreter`. Inspecting the generated file confirmed it only exports helpers like `py_binary`, `py_test`, and `compile_pip_requirements`.

If you need to pin the interpreter explicitly in 1.x, the correct label format is the platform-specific repo created by `python_register_toolchains`, e.g. `@python3_x86_64-unknown-linux-gnu//:python`. However, since this project has no third-party pip dependencies, the simplest fix was to drop the argument entirely and let `pip_parse` fall back to the system `python3`.

**Fix:**
Remove the stale load and the `python_interpreter_target` argument:

```python
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "python_deps",
    requirements_lock = "//:requirements.txt",
)
```

---

## Error 3: Missing root `BUILD` file and `requirements.txt`

**Error message:**
```
ERROR: Unable to load package for //:requirements.txt: BUILD file not found
in any of the following directories. Add a BUILD file to a directory to mark
it as a package.
 - /home/rogocorp/Src/bazel-bench/learn-bazel
```

**Cause:**
Two things were missing:

1. A `BUILD.bazel` (or `BUILD`) file in the workspace root — Bazel requires this to treat the root directory as a package, which is needed to resolve the `//:requirements.txt` label.
2. A `requirements.txt` file — `pip_parse` requires this file to exist even if it is empty.

**Fix:**
Create both files at the workspace root. Since the project has no pip dependencies, both can be empty:

```
touch BUILD.bazel
touch requirements.txt
```

---

## Final working `WORKSPACE.bazel`

```python
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "098ba13578e796c00c853a2161f382647f32eb9a77099e1c88bc5299333d0d6e",
    strip_prefix = "rules_python-1.9.0",
    url = "https://github.com/bazel-contrib/rules_python/releases/download/1.9.0/rules_python-1.9.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories", "python_register_toolchains")

py_repositories()

python_register_toolchains(
    name = "python3",
    python_version = "3.12",
)

load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "python_deps",
    requirements_lock = "//:requirements.txt",
)

load("@python_deps//:requirements.bzl", "install_deps")

install_deps()
```

---

## Key takeaways

- Bazel label syntax: always use `//package:file.bzl`, never `//package/file.bzl`.
- `rules_python` 1.x removed the `interpreter` export from the generated `defs.bzl`. Check the generated file directly when a symbol is missing — it is located at `$(bazel info output_base)/external/<repo_name>/defs.bzl`.
- Every directory referenced by a Bazel label (e.g. `//:file`) must contain a `BUILD` or `BUILD.bazel` file.
- When debugging WORKSPACE fetch errors, run `bazel build //...` and read errors top-to-bottom — each fix may reveal the next error.
