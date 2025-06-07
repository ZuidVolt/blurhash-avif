# main check (Enforced before commit)

format:
  ruff format --preview .

ruff-check:
  ruff check --fix --unsafe-fixes .

basedpyright-check:
    basedpyright .

mypy-strict-check:
    mypy --strict  .

pyrefly-check:
    pyrefly check .

check: format ruff-check basedpyright-check mypy-strict-check pyrefly-check

test:
    pytest -v tests/

# Build the package with uv
build:
	uv build

build-verbose:
	uv build --verbose

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/


# Additional analysis checks (not Enforced)

radon:
  radon cc -a -nc -s .

radon-mi:
  radon mi -s .

vulture:
  vulture . --min-confidence 60 --sort-by-size --exclude .venv

# Dependency management

sync-deps:
    uv sync --all-extras

check-uv-lock:
    [ -f ./uv.lock ] && uv lock --check || echo "No uv.lock file found, skipping lock check"

compile-user-dep:
    uv pip compile pyproject.toml -o requirements.sxt

compile-dev-dep:
    uv pip compile pyproject.toml --all-extras -o requirements-dev.txt

compile-dep: compile-user-dep compile-dev-dep check-uv-lock
