# Python Simple Rules Engine

<p align="center"><img height="200" alt="rogervila/python_simple_rules_engine" src="https://rogervila.es/static/img/python_simple_rules_engine.png" /></p>

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rogervila_python_simple_rules_engine&metric=coverage)](https://sonarcloud.io/dashboard?id=rogervila_python_simple_rules_engine)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=rogervila_python_simple_rules_engine&metric=alert_status)](https://sonarcloud.io/dashboard?id=rogervila_python_simple_rules_engine)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=rogervila_python_simple_rules_engine&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=rogervila_python_simple_rules_engine)


Evaluate rules based on a subject.


## Install

```sh
pip install python_simple_rules_engine
```

## Usage

The package expects a subject and a list of rules.

Each rule must be a class that extends `AbstractRule`.

The `subject` parameter can be any type of object (`Any`)

### Basic usage

Rules return a `Evaluation` object that should contain a `result` property defined by the user.

Also, the user can define the value of the `stop` property to determine if the evaluation process should stop or continue.

In this example, the `stop` property value does not affect the evaluation process since we are evaluating only one rule.

```py
from python_simple_rules_engine import AbstractRule, Evaluation, run

class FooRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        return Evaluation({
            'stop': False, # False by default. When set to True, the evaluation process is stopped.
            'result': (subject == 'foo') # Any. It should contain the evaluation result defined by the user.
        })

evaluation = run('foo', [FooRule()])

print(evaluation.result) # True
print(evaluation.rule) # FooRule instance
```

### Advanced usage

When evaluating multiple rules you can retrieve the historic of rules evaluated for a specific evaluation process by passing the `with_history` parameter as `True`.

The final `Evaluation` object will contain a `history` list with evaluations returned by the rules evaluated during the evaluation process.

Check `test_evaluation_with_history` method on `tests/test_python_simple_rules_engine.py` for a more detailed implementation.

```py
rules = [RuleA(), RuleB(), RuleC()]

# Let's pretend that the final evaluation comes from RuleC()
evaluation = run('C', rules, with_history=True)

print(len(evaluation.history)) # 2
print(evaluation.history[0].rule) # RuleA instance
print(evaluation.history[1].rule) # RuleB instance
```

## Examples

The examples are very simple for demo purposes, but they show the basic features this package comes with.

There is another python rules engine called [durable rules](https://github.com/jruizgit/rules) that comes with some examples. We will recreate them with this package.

### Pattern matching

Find a credit card type based on its number.

Check `test_match_example_with_cards` method on `tests/test_python_simple_rules_engine.py` for a more detailed implementation.

```py
class Card():
    def __init__(self, number):
        self.number = number

amex = Card('375678956789765')
visa = Card('4345634566789888')
mastercard = Card('2228345634567898')

class AmexRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        card_type = None

        if re.match(r"3[47][0-9]{13}", subject.number):
            card_type = 'amex'

        return Evaluation({'stop': (card_type != None), 'result': card_type})

class VisaRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        card_type = None

        if re.match(r"4[0-9]{12}([0-9]{3})?", subject.number):
            card_type = 'visa'

        return Evaluation({'stop': (card_type != None), 'result': card_type})

class MasterCardRule(AbstractRule):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        card_type = None

        if re.match(r"(5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|2720)[0-9]{12}", subject.number):
            card_type = 'mastercard'

        return Evaluation({'stop': (card_type != None), 'result': card_type})

# rules order does not affect the result.
rules = [AmexRule(), VisaRule(), MasterCardRule()]

evaluation = run(amex, rules)
print(evaluation.result) # 'amex'
print(evaluation.rule.__class__.__name__) # 'AmexRule'

evaluation = run(visa, rules)
print(evaluation.result) # 'visa'
print(evaluation.rule.__class__.__name__) # 'VisaRule'

evaluation = run(mastercard, rules)
print(evaluation.result) # 'mastercard'
print(evaluation.rule.__class__.__name__) # 'MasterCardRule'
```

### Set of facts

Define the type of an animal based on facts.

In this case, we will compare the current rule result with the previous evaluation result. If they match, we stop the evaluation process.

Check `test_facts_example` method on `tests/test_python_simple_rules_engine.py` for a more detailed implementation.

```py
class Animal():
    def __init__(self, eats, lives, color):
        self.eats = eats
        self.lives = lives
        self.color = color

frog = Animal('flies', 'water', 'green')
bird = Animal('worms', 'nest', 'black')

class EatsRule(AbstractRule):
    facts = {'flies': 'frog', 'worms': 'bird'}

    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        previous_result = previous_evaluation.result if previous_evaluation is not None else None
        current_result = self.facts[getattr(subject, 'eats')]

        return Evaluation({'stop': (previous_result == current_result), 'result': current_result})

class LivesRule(AbstractRule):
    facts = {'water': 'frog', 'nest': 'bird'}

    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        previous_result = previous_evaluation.result if previous_evaluation is not None else None
        current_result = self.facts[getattr(subject, 'lives')]

        return Evaluation({'stop': (previous_result == current_result), 'result': current_result})

class ColorRule(AbstractRule):
    facts = {'green': 'frog', 'black': 'bird'}

    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        previous_result = previous_evaluation.result if previous_evaluation is not None else None
        current_result = self.facts[getattr(subject, 'color')]

        return Evaluation({'stop': (previous_result == current_result), 'result': current_result})

# rules order does not affect the result.
rules = [EatsRule(), ColorRule(), LivesRule()]

evaluation = run(frog, rules)
print(evaluation.result) # 'frog'

evaluation = run(bird, rules)
print(evaluation.result) # 'bird'
```

## License

This project is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).

<div>Icons made by <a href="https://www.flaticon.com/authors/gregor-cresnar" title="Gregor Cresnar">Gregor Cresnar</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
