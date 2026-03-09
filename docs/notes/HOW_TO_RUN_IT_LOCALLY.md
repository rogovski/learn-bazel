# How to Run It Locally

## Command

```
bazel run //app:main
```

This builds and runs the Flask app defined in `app/BUILD.bazel`. It listens on `0.0.0.0:8080`.

## The `requirements.txt` Gotcha

`WORKSPACE.bazel` uses `pip_parse` with a `requirements_lock` file:

```python
pip_parse(
    name = "python_deps",
    requirements_lock = "//:requirements.txt",
)
```

Unlike a normal `pip install`, `pip_parse` does **not** resolve transitive dependencies automatically. Every package that Flask (or any dep) imports must be **explicitly listed** in `requirements.txt` — including transitive ones.

If you only list `Flask==3.0.3`, the build succeeds but the run fails with:

```
ModuleNotFoundError: No module named 'werkzeug'
```

because `werkzeug` is a Flask dependency that was never fetched by Bazel.

## Fix: Pin All Transitive Dependencies

Generate a complete lock file using a virtual environment:

```bash
python3 -m venv /tmp/env
/tmp/env/bin/pip install Flask==3.0.3
/tmp/env/bin/pip freeze > requirements.txt
```

The resulting `requirements.txt` should include all of Flask's transitive deps:

```
blinker==1.9.0
click==8.3.1
Flask==3.0.3
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
Werkzeug==3.1.6
```

After updating `requirements.txt`, Bazel will fetch all packages and the app will run correctly.

## Why the Root `BUILD.bazel` Must Exist (Even Empty)

Bazel defines a **package** as any directory that contains a `BUILD` or `BUILD.bazel` file. The root of the workspace is no exception.

`WORKSPACE.bazel` references a root-level file target using the label `//:requirements.txt`:

```python
pip_parse(
    name = "python_deps",
    requirements_lock = "//:requirements.txt",
)
```

The `//` prefix means "root package". For Bazel to recognize the root directory as a package — and therefore allow `//:requirements.txt` to be a valid label — a `BUILD.bazel` file must exist there. Without it, Bazel does not consider the root a package and cannot resolve the label, causing the build to fail.

The file can be completely empty; its mere presence is what matters.
