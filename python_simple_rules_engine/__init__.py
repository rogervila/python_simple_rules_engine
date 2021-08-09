#!/usr/bin/env python

import abc
from copy import deepcopy
from typing import Any, Optional


class AbstractData(abc.ABC):
    def __init__(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Evaluation(AbstractData):
    rule = None  # type: AbstractRule
    stop = False  # type: bool
    result = None  # type: Any
    extra = {}  # type: dict
    history = []  # type: list


class AbstractRule(abc.ABC):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        raise NotImplementedError


def run(subject, rules: list = [], with_history: bool = False) -> Optional[Evaluation]:
    evaluation = None

    for i, rule in enumerate(rules):
        if not isinstance(rule, AbstractRule):
            raise ValueError

        previous_evaluation = deepcopy(evaluation)

        evaluation = rule.evaluate(subject, previous_evaluation)
        evaluation.rule = rule

        if i > 0 and with_history:
            previous_evaluation.history = []
            evaluation.history.append(previous_evaluation)

        if evaluation.stop:
            break

    return evaluation
