import re
import unittest
from random import shuffle
from python_simple_rules_engine import AbstractRule, Evaluation, run


class test_python_simple_rules_engine(unittest.TestCase):
    def test_raises_value_error_if_list_contains_something_else_than_a_rule(self):
        with self.assertRaises(ValueError):
            rules = ['not a rule']
            run('the subject', rules)

    def test_returns_evaluation_with_result(self):
        class FooRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'result': (subject == 'foo')})

        rules = [FooRule()]

        evaluation = run('foo', rules)
        self.assertTrue(isinstance(evaluation, Evaluation))
        self.assertTrue(evaluation.result)

        evaluation = run('bar', rules)
        self.assertTrue(isinstance(evaluation, Evaluation))
        self.assertFalse(evaluation.result)

    def test_returns_none_if_rules_list_is_empty(self):
        rules = []
        evaluation = run('the subject', rules)

        self.assertIsNone(evaluation)

    def test_stops_when_defined(self):
        class StopRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': True, 'result': 'stopped'})

        class NeverReachedRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'never reached'})

        rules = [StopRule(), NeverReachedRule()]
        evaluation = run('the subject', rules)

        self.assertEqual(
            evaluation.rule.__class__.__name__,
            'StopRule'
        )

    def test_evaluation_extra_field(self):
        class TestRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'extra': {'foo': 'bar'}})

        rules = [TestRule()]
        evaluation = run('the subject', rules)

        self.assertEqual(evaluation.extra['foo'], 'bar')

    # https://github.com/jruizgit/rules#python-2
    def test_match_example_with_cards(self):
        class Card():
            def __init__(self, number):
                self.number = number

        amex = Card('375678956789765')
        visa = Card('4345634566789888')
        mastercard = Card('2228345634567898')

        class AmexRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                card_type = None

                if not isinstance(subject, Card):
                    raise ValueError

                if re.match(r"3[47][0-9]{13}", subject.number):
                    card_type = 'amex'

                return Evaluation({'stop': (card_type != None), 'result': card_type})

        class VisaRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                card_type = None

                if not isinstance(subject, Card):
                    raise ValueError

                if re.match(r"4[0-9]{12}([0-9]{3})?", subject.number):
                    card_type = 'visa'

                return Evaluation({'stop': (card_type != None), 'result': card_type})

        class MasterCardRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                card_type = None

                if not isinstance(subject, Card):
                    raise ValueError

                if re.match(r"(5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|2720)[0-9]{12}", subject.number):
                    card_type = 'mastercard'

                return Evaluation({'stop': (card_type != None), 'result': card_type})

        rules = [AmexRule(), VisaRule(), MasterCardRule()]

        # Shuffle rules order to assert that rules order does not change the output
        for _ in range(10):
            shuffle(rules)
            # print([rule.__class__.__name__ for rule in rules])

            evaluation = run(amex, rules)
            self.assertEqual(evaluation.result, 'amex')
            self.assertEqual(evaluation.rule.__class__.__name__, 'AmexRule')

            evaluation = run(visa, rules)
            self.assertEqual(evaluation.result, 'visa')
            self.assertEqual(evaluation.rule.__class__.__name__, 'VisaRule')

            evaluation = run(mastercard, rules)
            self.assertEqual(evaluation.result, 'mastercard')
            self.assertEqual(evaluation.rule.__class__.__name__, 'MasterCardRule')  # nopep8

    def test_facts_example(self):
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
                if not isinstance(subject, Animal):
                    raise ValueError

                previous_result = previous_evaluation.result if previous_evaluation is not None else None
                current_result = self.facts[getattr(subject, 'eats')]

                return Evaluation({'stop': (previous_result == current_result), 'result': current_result})

        class LivesRule(AbstractRule):
            facts = {'water': 'frog', 'nest': 'bird'}

            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                if not isinstance(subject, Animal):
                    raise ValueError

                previous_result = previous_evaluation.result if previous_evaluation is not None else None
                current_result = self.facts[getattr(subject, 'lives')]

                return Evaluation({'stop': (previous_result == current_result), 'result': current_result})

        class ColorRule(AbstractRule):
            facts = {'green': 'frog', 'black': 'bird'}

            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                if not isinstance(subject, Animal):
                    raise ValueError

                previous_result = previous_evaluation.result if previous_evaluation is not None else None
                current_result = self.facts[getattr(subject, 'color')]

                return Evaluation({'stop': (previous_result == current_result), 'result': current_result})

        rules = [EatsRule(), ColorRule(), LivesRule()]

        # Shuffle rules order to assert that rules order does not change the output
        for _ in range(10):
            shuffle(rules)

            evaluation = run(frog, rules)

            self.assertEqual(evaluation.result, 'frog')
            self.assertEqual(
                evaluation.rule.__class__.__name__,
                rules[1].__class__.__name__
            )

            evaluation = run(bird, rules)
            self.assertEqual(evaluation.result, 'bird')
            self.assertEqual(
                evaluation.rule.__class__.__name__,
                rules[1].__class__.__name__
            )

    def test_evaluation_with_history(self):
        class RuleA(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'a'})

        class RuleB(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'b'})

        class RuleC(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'c'})

        rules = [RuleA(), RuleB(), RuleC()]

        evaluation = run('the subject', rules, with_history=True)

        self.assertEqual(len(evaluation.history), 2)

        self.assertEqual(
            evaluation.history[0].rule.__class__.__name__,
            'RuleA'
        )
        self.assertEqual(
            evaluation.history[0].result,
            'a'
        )
        self.assertEqual(len(evaluation.history[0].history), 0)

        self.assertEqual(
            evaluation.history[1].rule.__class__.__name__,
            'RuleB'
        )
        self.assertEqual(
            evaluation.history[1].result,
            'b'
        )
        self.assertEqual(len(evaluation.history[1].history), 0)

    def test_multiple_subjects(self):
        class RuleA(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'a'})

        class RuleB(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'b'})

        class RuleC(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'c'})

        rules = [RuleA(), RuleB(), RuleC()]
        subjects = ['a', 'b', 'c']

        for x, subject in enumerate(subjects):
            evaluation = run(subject, rules, with_history=True)

            for y, history in enumerate(evaluation.history):
                print(f'\nSUBJECT {x} HISTORY {y} RULE: "{history.rule.__class__.__name__}"')  # nopep8

        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
