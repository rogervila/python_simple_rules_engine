#!/usr/bin/env python

import abc
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


class AbstractRule(abc.ABC):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        raise NotImplementedError


def run(subject, rules: list = []) -> Optional[Evaluation]:
    evaluation = None

    for rule in rules:
        if not isinstance(rule, AbstractRule):
            raise ValueError

        evaluation = rule.evaluate(subject, evaluation)
        evaluation.rule = rule

        if evaluation.stop:
            break

    return evaluation
