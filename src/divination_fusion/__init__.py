"""Evidence-driven multi-agent divination harness."""


def run_analysis(*args, **kwargs):
    from .workflow import run_analysis as _run_analysis

    return _run_analysis(*args, **kwargs)


__all__ = ["run_analysis"]
