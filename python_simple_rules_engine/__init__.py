#!/usr/bin/env python

import abc
from typing import Any, Optional


class AbstractData(abc.ABC):
    def __init__(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class AbstractSubject(abc.ABC):
    pass


class Evaluation(AbstractData):
    rule = None  # type: AbstractRule
    stop = False  # type: bool
    result = None  # type: Any


class AbstractRule(abc.ABC):
    def evaluate(self, subject: AbstractSubject) -> Evaluation:
        raise NotImplementedError


def run(subject: AbstractSubject, rules: list) -> Optional[Evaluation]:
    evaluation = None

    for rule in rules:
        if not isinstance(rule, AbstractRule):
            raise ValueError

        evaluation = rule.evaluate(subject)

        if evaluation.stop:
            evaluation.rule = rule
            break

    return evaluation
