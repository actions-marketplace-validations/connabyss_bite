"""The slowest tests start first, so pytest -n auto's workers don't end with one of them running alone while the
others wait (Windows CI ended with three self-test parts in a row on one worker, 2026-11-04)."""

SLOW_FIRST = ("test_selftest.py", "test_rerun_failed_only_other_languages.py", "test_jobs_memory.py",
              "test_rust_unit_tests.py")


def pytest_collection_modifyitems(items):
    items.sort(key=lambda item: 0 if item.path.name in SLOW_FIRST else 1)  # stable: the rest keep their order
