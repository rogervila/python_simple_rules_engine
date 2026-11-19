#!/usr/bin/env python

# Public API
__all__ = ["AbstractData", "AbstractRule", "Evaluation", "run"]

# ---------------------------------------------------------------------------
# Lazy-loaded stdlib dependencies (PEP 562 – supported since Python 3.7).
# Modules are imported on first attribute access and then cached in globals()
# so subsequent accesses are O(1) dict lookups.
# ---------------------------------------------------------------------------
_LAZY_MODULES: dict = {
    "abc": "abc",
    "copy": "copy",
}

_LAZY_ATTRS: dict = {
    "Any": ("typing", "Any"),
    "Optional": ("typing", "Optional"),
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        import importlib
        module = importlib.import_module(_LAZY_MODULES[name])
        globals()[name] = module
        return module

    if name in _LAZY_ATTRS:
        import importlib
        mod_name, attr = _LAZY_ATTRS[name]
        module = importlib.import_module(mod_name)
        value = getattr(module, attr)
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    base = list(globals().keys())
    return sorted(set(base + list(_LAZY_MODULES) + list(_LAZY_ATTRS) + __all__))


# ---------------------------------------------------------------------------
# Core implementation
# ---------------------------------------------------------------------------

import abc as _abc
from copy import copy as _copy
from typing import Any as _Any, Optional as _Optional


class AbstractData(_abc.ABC):
    def __init__(self, data: dict) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Evaluation(AbstractData):
    rule: _Optional["AbstractRule"] = None
    stop: bool = False
    result: _Optional[_Any] = None
    extra: dict = {}
    history: list = []


class AbstractRule(_abc.ABC):
    def evaluate(
        self,
        subject: _Any,
        previous_evaluation: _Optional[Evaluation] = None,
    ) -> Evaluation:
        raise NotImplementedError


def run(
    subject: _Any,
    rules: list = [],
    with_history: bool = False,
) -> _Optional[Evaluation]:
    evaluation: _Optional[Evaluation] = None
    previous_evaluation: _Optional[Evaluation] = None
    history: list = []

    for i, rule in enumerate(rules):
        if not isinstance(rule, AbstractRule):
            raise ValueError

        previous_evaluation = _copy(evaluation)

        evaluation = rule.evaluate(subject, previous_evaluation)
        evaluation.rule = rule

        if i > 0 and with_history:
            history.append(previous_evaluation)

        if evaluation.stop:
            break

    if evaluation is not None:
        evaluation.history = history

    return evaluation
