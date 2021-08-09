import re
import unittest
from random import shuffle
import python_simple_rules_engine
from python_simple_rules_engine import AbstractRule, Evaluation


class test_python_simple_rules_engine(unittest.TestCase):
    def test_raises_value_error_if_list_contains_something_else_than_a_rule(self):
        with self.assertRaises(ValueError):
            rules = ['not a rule']

            python_simple_rules_engine.run('the subject', rules)

    def test_returns_evaluation_with_result(self):
        class TestRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'result': 'whatever'})

        rules = [TestRule()]
        evaluation = python_simple_rules_engine.run('the subject', rules)

        self.assertTrue(isinstance(evaluation, Evaluation))
        self.assertEqual(evaluation.result, 'whatever')

    def test_stops_when_defined(self):
        class StopRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': True, 'result': 'stopped'})

        class NeverReachedRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': False, 'result': 'never reached'})

        rules = [StopRule(), NeverReachedRule()]
        evaluation = python_simple_rules_engine.run('the subject', rules)

        self.assertEqual(
            evaluation.rule.__class__.__name__,
            'StopRule'
        )

    def test_evaluation_extra_field(self):
        class TestRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'extra': {'foo': 'bar'}})

        rules = [TestRule()]
        evaluation = python_simple_rules_engine.run('the subject', rules)

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

            evaluation = python_simple_rules_engine.run(amex, rules)
            self.assertEqual(evaluation.result, 'amex')
            self.assertEqual(evaluation.rule.__class__.__name__, 'AmexRule')

            evaluation = python_simple_rules_engine.run(visa, rules)
            self.assertEqual(evaluation.result, 'visa')
            self.assertEqual(evaluation.rule.__class__.__name__, 'VisaRule')

            evaluation = python_simple_rules_engine.run(mastercard, rules)
            self.assertEqual(evaluation.result, 'mastercard')
            self.assertEqual(evaluation.rule.__class__.__name__, 'MasterCardRule')  # nopep8

    def test_example_with_assert_facts(self):
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

            evaluation = python_simple_rules_engine.run(frog, rules)

            self.assertEqual(evaluation.result, 'frog')
            self.assertEqual(
                evaluation.rule.__class__.__name__,
                rules[1].__class__.__name__
            )

            evaluation = python_simple_rules_engine.run(bird, rules)
            self.assertEqual(evaluation.result, 'bird')
            self.assertEqual(
                evaluation.rule.__class__.__name__,
                rules[1].__class__.__name__
            )


if __name__ == '__main__':
    unittest.main()
