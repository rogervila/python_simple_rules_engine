import unittest
from python_simple_rules_engine import Evaluation, AbstractRule


class test_evaluation(unittest.TestCase):
    def test_raises_type_error_stop_is_not_a_bool(self):
        with self.assertRaises(TypeError):
            Evaluation({
                'stop': 'not a bool',
            })

        evaluation = Evaluation({'stop': True})
        self.assertTrue(evaluation.stop)

    def test_raises_type_error_rule_is_not_an_abstract_rule(self):
        with self.assertRaises(TypeError):
            Evaluation({
                'rule': 'not an abstract_rule',
            })

            class FooRule(AbstractRule):
                pass

            evaluation = Evaluation({'rule': FooRule()})
            self.assertIsInstance(evaluation.rule, AbstractRule)

    def test_raises_type_error_extra_is_not_a_dict(self):
        with self.assertRaises(TypeError):
            Evaluation({
                'extra': 'not a dict',
            })

        evaluation = Evaluation({'extra': {}})
        self.assertIsInstance(evaluation.extra, dict)

    def test_raises_type_error_history_is_not_a_list(self):
        with self.assertRaises(TypeError):
            Evaluation({
                'history': 'not a list',
            })

        evaluation = Evaluation({'history': []})
        self.assertIsInstance(evaluation.history, list)
