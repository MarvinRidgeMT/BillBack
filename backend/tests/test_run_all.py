"""eval/run_all.py: a step that can't even be imported is reported, and the other steps still run."""

from eval import run_all


def test_broken_eval_module_is_a_failed_step_not_a_crash(monkeypatch):
    """Graphify review: an ImportError used to abort the whole run before RESULTS.md was written."""
    ran = []
    monkeypatch.setattr(run_all, "run_pytest", lambda: ran.append("pytest"))
    monkeypatch.setattr(run_all, "_main_of", lambda name: (lambda argv: ran.append(name)) if name != "policy_grounding"
                        else run_all.__dict__["_broken"])
    run_all._broken = lambda argv: __import__("eval.no_such_module")
    errors = run_all.run_steps(offline=True, runs=1)
    assert errors["grounding"] and "No module named" in errors["grounding"]
    assert "run_households" in ran and "pytest" in ran
