import re
import unittest
from random import shuffle
import python_simple_rules_engine
from python_simple_rules_engine import (AbstractRule, AbstractSubject, Evaluation)  # nopep8


class test_python_simple_rules_engine(unittest.TestCase):
    def test_raises_value_error_if_list_contains_something_else_than_a_rule(self):
        with self.assertRaises(ValueError):
            class TestSubject(AbstractSubject):
                pass

            rules = ['not a rule']

            python_simple_rules_engine.run(TestSubject(), rules)

    def test_returns_evaluation_with_result(self):
        class TestSubject(AbstractSubject):
            pass

        class TestRule(AbstractRule):
            def evaluate(self, subject: AbstractSubject) -> Evaluation:
                return Evaluation({'stop': True, 'result': 'whatever'})

        rules = [TestRule()]
        evaluation = python_simple_rules_engine.run(TestSubject(), rules)

        self.assertTrue(isinstance(evaluation, Evaluation))
        self.assertEqual(evaluation.result, 'whatever')

    # https://github.com/jruizgit/rules#python-2
    def test_example_with_card_types(self):
        class AbstractCard(AbstractRule):
            number = None

        class Amex(AbstractCard):
            number = '375678956789765'

        class Visa(AbstractCard):
            number = '4345634566789888'

        class MasterCard(AbstractCard):
            number = '2228345634567898'

        class AmexRule(AbstractRule):
            def evaluate(self, subject: AbstractSubject) -> Evaluation:
                card_type = None

                if not isinstance(subject, AbstractCard):
                    raise ValueError

                if re.match(r"3[47][0-9]{13}", subject.number):
                    card_type = 'amex'

                return Evaluation({'stop': (card_type != None), 'result': card_type})

        class VisaRule(AbstractRule):
            def evaluate(self, subject: AbstractSubject) -> Evaluation:
                card_type = None

                if not isinstance(subject, AbstractCard):
                    raise ValueError

                if re.match(r"4[0-9]{12}([0-9]{3})?", subject.number):
                    card_type = 'visa'

                return Evaluation({'stop': (card_type != None), 'result': card_type})

        class MasterCardRule(AbstractRule):
            def evaluate(self, subject: AbstractSubject) -> Evaluation:
                card_type = None

                if not isinstance(subject, AbstractCard):
                    raise ValueError

                if re.match(r"(5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|2720)[0-9]{12}", subject.number):
                    card_type = 'mastercard'

                return Evaluation({'stop': (card_type != None), 'result': card_type})

        rules = [AmexRule(), VisaRule(), MasterCardRule()]

        # Shuffle rules order to assert that, in this case, rules order does not change the output
        for _ in range(10):
            shuffle(rules)
            # print([rule.__class__.__name__ for rule in rules])

            evaluation = python_simple_rules_engine.run(Amex(), rules)
            self.assertEqual(evaluation.result, 'amex')
            self.assertEqual(evaluation.rule.__class__.__name__, 'AmexRule')

            evaluation = python_simple_rules_engine.run(Visa(), rules)
            self.assertEqual(evaluation.result, 'visa')
            self.assertEqual(evaluation.rule.__class__.__name__, 'VisaRule')

            evaluation = python_simple_rules_engine.run(MasterCard(), rules)
            self.assertEqual(evaluation.result, 'mastercard')
            self.assertEqual(evaluation.rule.__class__.__name__, 'MasterCardRule')  # nopep8


if __name__ == '__main__':
    unittest.main()
