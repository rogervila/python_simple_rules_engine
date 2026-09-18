# Python Simple Rules Engine

<p align="center"><img height="200" alt="rogervila/python_simple_rules_engine" src="https://rogervila.es/static/img/python_simple_rules_engine.png" /></p>

[![PyPI version](https://badge.fury.io/py/python-simple-rules-engine.svg)](https://badge.fury.io/py/python-simple-rules-engine)
![PyPI - Downloads](https://img.shields.io/pypi/dm/python-simple-rules-engine)

A small, dependency-free engine for evaluating an ordered sequence of Python rules against any subject.

## Install

```sh
pip install python_simple_rules_engine
```

The package supports Python 3.9 and later.

## Core Concepts

Pass a subject and an ordered list of `AbstractRule` instances to `run`. Each rule returns an `Evaluation`. Rules can inspect the preceding evaluation and can stop further processing.

| Type | Purpose |
| --- | --- |
| `AbstractRule` | Base class for user-defined rules. Override `evaluate`. |
| `Evaluation` | The value a rule returns: its result, stop decision, optional metadata, and eventually its producing rule. |
| `run` | Evaluates rules in order and returns the final `Evaluation`, or `None` for an empty rule list. |

### `Evaluation` fields

Construct an evaluation with a dictionary. Only the following keys are accepted; unknown keys are ignored.

| Field | Default | Meaning |
| --- | --- | --- |
| `result` | `None` | Application-defined output of the rule. |
| `stop` | `False` | When truthy, stops evaluation after this rule. |
| `extra` | `{}` | Optional application-defined metadata. |
| `rule` | `None` | Set by `run` to the rule that produced the evaluation. |
| `history` | `[]` | Set by `run` when it returns the final evaluation. |

## Basic Usage

```python
from typing import Any

from python_simple_rules_engine import AbstractRule, Evaluation, run


class IsFooRule(AbstractRule):
    def evaluate(
        self, subject: Any, previous_evaluation: Evaluation = None
    ) -> Evaluation:
        return Evaluation({
            "result": subject == "foo",
        })


evaluation = run("foo", [IsFooRule()])

print(evaluation.result)  # True
print(type(evaluation.rule).__name__)  # IsFooRule
```

`result` can hold any value your application needs. A rule does not need to set every field because the defaults above apply.

## Chaining Rules

The second and later rules receive a shallow copy of the preceding evaluation. This makes it straightforward to accumulate or compare decisions.

```python
from python_simple_rules_engine import AbstractRule, Evaluation, run


class Account:
    def __init__(self, has_debt):
        self.has_debt = has_debt


class ReadStatusRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation=None):
        status = "active" if subject.has_debt is False else "inactive"
        return Evaluation({"result": status})


class ApproveActiveRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation=None):
        approved = previous_evaluation.result == "active"
        return Evaluation({"result": approved, "stop": approved})


class DenyInactiveRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation=None):
        return Evaluation({"result": False, "stop": True})


evaluation = run(
    Account(has_debt=False),
    [ReadStatusRule(), ApproveActiveRule(), DenyInactiveRule()],
)

print(evaluation.result)  # True
print(type(evaluation.rule).__name__)  # ApproveActiveRule

evaluation = run(
    Account(has_debt=True),
    [ReadStatusRule(), ApproveActiveRule(), DenyInactiveRule()],
)

print(evaluation.result)  # False
print(type(evaluation.rule).__name__)  # DenyInactiveRule
```

Rules run in list order. The first rule receives `None` as `previous_evaluation`. Processing ends immediately after a rule returns an evaluation with a truthy `stop` field; rules after it are not called.

## Examples

### Card Type Detection

Use ordered rules to identify a credit-card type from its number. Each matching rule stops the engine, so the final evaluation identifies the matching rule and card type.

```python
import re

from python_simple_rules_engine import AbstractRule, Evaluation, run


class Card:
    def __init__(self, number):
        self.number = number


class AmexRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation=None):
        card_type = None
        if re.match(r"3[47][0-9]{13}", subject.number):
            card_type = "amex"
        return Evaluation({"stop": card_type is not None, "result": card_type})


class VisaRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation=None):
        card_type = None
        if re.match(r"4[0-9]{12}([0-9]{3})?", subject.number):
            card_type = "visa"
        return Evaluation({"stop": card_type is not None, "result": card_type})


class MasterCardRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation=None):
        card_type = None
        if re.match(
            r"(5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|2720)[0-9]{12}",
            subject.number,
        ):
            card_type = "mastercard"
        return Evaluation({"stop": card_type is not None, "result": card_type})


rules = [AmexRule(), VisaRule(), MasterCardRule()]

evaluation = run(Card("375678956789765"), rules)
print(evaluation.result)  # amex
print(type(evaluation.rule).__name__)  # AmexRule

evaluation = run(Card("4345634566789888"), rules)
print(evaluation.result)  # visa

evaluation = run(Card("2228345634567898"), rules)
print(evaluation.result)  # mastercard
```

### Animal Facts

Rules can compare a fact with the preceding result. Here, a matching conclusion stops the engine; therefore the rules may be listed in any order as long as the facts agree.

```python
from python_simple_rules_engine import AbstractRule, Evaluation, run


class Animal:
    def __init__(self, eats, lives, color):
        self.eats = eats
        self.lives = lives
        self.color = color


class EatsRule(AbstractRule):
    facts = {"flies": "frog", "worms": "bird"}

    def evaluate(self, subject, previous_evaluation=None):
        previous_result = (
            previous_evaluation.result if previous_evaluation is not None else None
        )
        current_result = self.facts[subject.eats]
        return Evaluation({
            "stop": previous_result == current_result,
            "result": current_result,
        })


class LivesRule(AbstractRule):
    facts = {"water": "frog", "nest": "bird"}

    def evaluate(self, subject, previous_evaluation=None):
        previous_result = (
            previous_evaluation.result if previous_evaluation is not None else None
        )
        current_result = self.facts[subject.lives]
        return Evaluation({
            "stop": previous_result == current_result,
            "result": current_result,
        })


class ColorRule(AbstractRule):
    facts = {"green": "frog", "black": "bird"}

    def evaluate(self, subject, previous_evaluation=None):
        previous_result = (
            previous_evaluation.result if previous_evaluation is not None else None
        )
        current_result = self.facts[subject.color]
        return Evaluation({
            "stop": previous_result == current_result,
            "result": current_result,
        })


rules = [EatsRule(), ColorRule(), LivesRule()]

evaluation = run(Animal("flies", "water", "green"), rules)
print(evaluation.result)  # frog

evaluation = run(Animal("worms", "nest", "black"), rules)
print(evaluation.result)  # bird
```

## Evaluation History

Set `with_history=True` to receive the evaluations produced before the final one. History contains only rules that actually ran, so it respects early stopping.

```python
evaluation = run(
    "foo",
    [FirstRule(), SecondRule(), FinalRule()],
    with_history=True,
)

len(evaluation.history)  # 2
evaluation.history[0].rule  # FirstRule instance
evaluation.history[1].rule  # SecondRule instance
```

History entries are shallow copies of preceding evaluations. If a rule stores mutable values in `result` or `extra`, later mutations to those nested values remain visible through history.

## Rule Requirements And Errors

- Every item in `rules` must be an `AbstractRule` instance. Otherwise, `run` raises `ValueError`.
- Each rule must override `evaluate(subject, previous_evaluation)` and return an `Evaluation` instance.
- An empty `rules` list returns `None`.
- The engine does not catch exceptions raised by a rule; validation and domain errors should be handled by the rule or its caller.

## Development

Run the unit test suite from the repository root:

```sh
python -m unittest discover -v
```

The tests exercise the public execution contract, including invalid rules, evaluation defaults, stopping, rule chaining, and history behavior.

## License

This project is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).

<div>Icons made by <a href="https://www.flaticon.com/authors/gregor-cresnar" title="Gregor Cresnar">Gregor Cresnar</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
