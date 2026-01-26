import pytest


@pytest.fixture(scope="session")
def tasks() -> list[str]:
    """List of discovered pf tasks (used by some legacy tests)."""
    try:
        import pf_parser  # type: ignore

        dsl_src, task_sources = pf_parser._load_pfy_source_with_includes(file_arg=None)
        tasks_dict = pf_parser.parse_pfyfile_text(dsl_src, task_sources)
        return list(tasks_dict.keys())
    except Exception:
        return []

