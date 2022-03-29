#!/usr/bin/env python

import abc
from copy import copy
from typing import Any, Optional
from py_dto import DTO


class AbstractData(abc.ABC):
    def __init__(self, data: dict):
        data = Data(data).to_dict()
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


class Data(DTO):
    rule: Optional[AbstractRule]
    stop: Optional[bool]
    result: Any
    extra: Optional[dict]
    history: Optional[list]

    def to_dict(self) -> dict:
        return {
            'rule': self.rule if hasattr(self, 'rule') else None,
            'stop': self.stop if hasattr(self, 'stop') else False,
            'result': self.result if hasattr(self, 'result') else None,
            'extra': self.extra if hasattr(self, 'extra') else {},
            'history': self.history if hasattr(self, 'history') else [],
        }


def run(subject, rules: list = [], with_history: bool = False) -> Optional[Evaluation]:
    evaluation = None
    previous_evaluation = None
    history = []

    for i, rule in enumerate(rules):
        if not isinstance(rule, AbstractRule):
            raise ValueError

        previous_evaluation = copy(evaluation)

        evaluation = rule.evaluate(subject, previous_evaluation)
        evaluation.rule = rule

        if i > 0 and with_history:
            history.append(previous_evaluation)

        if evaluation.stop:
            break

    if evaluation is not None:
        evaluation.history = history

    return evaluation
