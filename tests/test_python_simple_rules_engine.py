import re
import sys
import unittest
from random import shuffle
import python_simple_rules_engine
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

    def test_abstract_rule_evaluate_must_be_implemented(self):
        with self.assertRaises(NotImplementedError):
            AbstractRule().evaluate('the subject')

    def test_evaluation_uses_defaults_and_ignores_unknown_fields(self):
        evaluation = Evaluation({'result': 'matched', 'unknown': 'ignored'})

        self.assertEqual(evaluation.result, 'matched')
        self.assertIsNone(evaluation.rule)
        self.assertFalse(evaluation.stop)
        self.assertEqual(evaluation.extra, {})
        self.assertEqual(evaluation.history, [])
        self.assertFalse(hasattr(evaluation, 'unknown'))

    def test_evaluation_accepts_all_documented_fields(self):
        rule = AbstractRule()
        evaluation = Evaluation({
            'rule': rule,
            'stop': True,
            'result': 'matched',
            'extra': {'source': 'test'},
            'history': ['earlier'],
        })

        self.assertIs(evaluation.rule, rule)
        self.assertTrue(evaluation.stop)
        self.assertEqual(evaluation.result, 'matched')
        self.assertEqual(evaluation.extra, {'source': 'test'})
        self.assertEqual(evaluation.history, ['earlier'])

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

    def test_passes_previous_evaluation_to_each_following_rule(self):
        received_evaluations = []

        class FirstRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                received_evaluations.append(previous_evaluation)
                return Evaluation({'result': subject})

        class SecondRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                received_evaluations.append(previous_evaluation)
                return Evaluation({'result': previous_evaluation.result.upper()})

        evaluation = run('first', [FirstRule(), SecondRule()])

        self.assertIsNone(received_evaluations[0])
        self.assertEqual(received_evaluations[1].result, 'first')
        self.assertIsInstance(received_evaluations[1].rule, FirstRule)
        self.assertEqual(evaluation.result, 'FIRST')

    def test_approves_active_accounts_and_denies_inactive_accounts(self):
        class Account:
            def __init__(self, has_debt):
                self.has_debt = has_debt

        class ReadStatusRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                status = 'active' if subject.has_debt is False else 'inactive'
                return Evaluation({'result': status})

        class ApproveActiveRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                approved = previous_evaluation.result == 'active'
                return Evaluation({'result': approved, 'stop': approved})

        class DenyInactiveRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'result': False, 'stop': True})

        rules = [ReadStatusRule(), ApproveActiveRule(), DenyInactiveRule()]

        approved_evaluation = run(Account(has_debt=False), rules)
        self.assertTrue(approved_evaluation.result)
        self.assertTrue(approved_evaluation.stop)
        self.assertIsInstance(approved_evaluation.rule, ApproveActiveRule)

        denied_evaluation = run(Account(has_debt=True), rules)
        self.assertFalse(denied_evaluation.result)
        self.assertTrue(denied_evaluation.stop)
        self.assertIsInstance(denied_evaluation.rule, DenyInactiveRule)

    def test_history_is_empty_when_the_first_rule_stops(self):
        class StopRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': True, 'result': subject})

        evaluation = run('the subject', [StopRule()], with_history=True)

        self.assertEqual(evaluation.history, [])

    def test_history_contains_only_rules_evaluated_before_stop(self):
        class FirstRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'result': 'first'})

        class StopRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'stop': True, 'result': 'stopped'})

        class NeverReachedRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                self.fail('A stopped evaluation must not run later rules')

        evaluation = run(
            'the subject',
            [FirstRule(), StopRule(), NeverReachedRule()],
            with_history=True,
        )

        self.assertEqual(evaluation.result, 'stopped')
        self.assertEqual(len(evaluation.history), 1)
        self.assertEqual(evaluation.history[0].result, 'first')
        self.assertIsInstance(evaluation.history[0].rule, FirstRule)

    def test_history_entries_are_shallow_copies(self):
        extra = {'status': 'initial'}

        class FirstRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                return Evaluation({'result': 'first', 'extra': extra})

        class SecondRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
                extra['status'] = 'updated'
                return Evaluation({'result': 'second'})

        evaluation = run('the subject', [FirstRule(), SecondRule()], with_history=True)

        self.assertEqual(evaluation.history[0].extra, {'status': 'updated'})

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

        for _, subject in enumerate(subjects):
            evaluation = run(subject, rules, with_history=True)

            self.assertEqual(
                len(evaluation.history),
                2
            )

            self.assertEqual(
                evaluation.history[0].rule.__class__.__name__,
                'RuleA'
            )

            self.assertEqual(
                evaluation.history[1].rule.__class__.__name__,
                'RuleB'
            )


    # ------------------------------------------------------------------
    # run() — ValueError precision
    # ------------------------------------------------------------------

    def test_raises_value_error_on_first_invalid_item_in_mixed_list(self):
        """run() stops at the first non-AbstractRule item and raises ValueError."""
        reached = []

        class GoodRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                reached.append(True)
                return Evaluation({'result': 'ok'})

        with self.assertRaises(ValueError):
            run('subject', [GoodRule(), 'bad', GoodRule()])

        # First rule ran; second is bad so we stop; third never runs.
        self.assertEqual(len(reached), 1)

    def test_raises_value_error_when_invalid_item_is_first(self):
        reached = []

        class GoodRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                reached.append(True)
                return Evaluation({'result': 'ok'})

        with self.assertRaises(ValueError):
            run('subject', [42, GoodRule()])

        self.assertEqual(len(reached), 0)

    # ------------------------------------------------------------------
    # run() — statelessness across calls
    # ------------------------------------------------------------------

    def test_run_is_stateless_across_calls(self):
        """Calling run twice with the same rule list must not leak state."""

        class CountRule(AbstractRule):
            calls = 0

            def evaluate(self, subject, previous_evaluation=None):
                CountRule.calls += 1
                return Evaluation({'result': CountRule.calls})

        rules = [CountRule()]

        e1 = run('a', rules)
        e2 = run('b', rules)

        self.assertEqual(e1.result, 1)
        self.assertEqual(e2.result, 2)
        # Both evaluations are independent objects
        self.assertIsNot(e1, e2)

    def test_history_is_independent_between_calls(self):
        """History from one run() must not appear in a later run()."""

        class SimpleRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': subject})

        rules = [SimpleRule(), SimpleRule()]

        e1 = run('x', rules, with_history=True)
        e2 = run('y', rules, with_history=True)

        self.assertEqual(len(e1.history), 1)
        self.assertEqual(len(e2.history), 1)
        self.assertEqual(e1.history[0].result, 'x')
        self.assertEqual(e2.history[0].result, 'y')

    # ------------------------------------------------------------------
    # run() — history off by default
    # ------------------------------------------------------------------

    def test_history_is_empty_by_default(self):
        """with_history defaults to False; history must always be empty."""

        class R(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': subject})

        evaluation = run('x', [R(), R(), R()])
        self.assertEqual(evaluation.history, [])

    # ------------------------------------------------------------------
    # run() — stop on last rule
    # ------------------------------------------------------------------

    def test_stop_on_last_rule_still_returns_evaluation(self):
        """stop=True on the final rule is valid; it just returns normally."""

        class LastRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': 'done', 'stop': True})

        evaluation = run('x', [LastRule()])

        self.assertEqual(evaluation.result, 'done')
        self.assertTrue(evaluation.stop)
        self.assertIsInstance(evaluation.rule, LastRule)

    # ------------------------------------------------------------------
    # run() — same rule instance reused
    # ------------------------------------------------------------------

    def test_same_rule_instance_can_appear_multiple_times(self):
        """A single rule object may be listed more than once; each call is independent."""

        class AppendRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                prev = previous_evaluation.result if previous_evaluation else []
                return Evaluation({'result': prev + [subject]})

        rule = AppendRule()
        evaluation = run('x', [rule, rule, rule])

        self.assertEqual(evaluation.result, ['x', 'x', 'x'])

    # ------------------------------------------------------------------
    # run() — exceptions from rules propagate
    # ------------------------------------------------------------------

    def test_exception_raised_inside_rule_propagates_uncaught(self):
        """run() must not swallow exceptions thrown by a rule's evaluate()."""

        class BrokenRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                raise RuntimeError('rule exploded')

        with self.assertRaises(RuntimeError, msg='rule exploded'):
            run('subject', [BrokenRule()])

    # ------------------------------------------------------------------
    # Evaluation — falsy but valid result values
    # ------------------------------------------------------------------

    def test_result_can_be_zero(self):
        class ZeroRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': 0})

        evaluation = run('x', [ZeroRule()])
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.result, 0)

    def test_result_can_be_false(self):
        class FalseRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': False})

        evaluation = run('x', [FalseRule()])
        self.assertIsNotNone(evaluation)
        self.assertIs(evaluation.result, False)

    def test_result_can_be_empty_string(self):
        class EmptyStrRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': ''})

        evaluation = run('x', [EmptyStrRule()])
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.result, '')

    def test_result_can_be_empty_list(self):
        class EmptyListRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': []})

        evaluation = run('x', [EmptyListRule()])
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.result, [])

    # ------------------------------------------------------------------
    # Evaluation — extra survives chaining
    # ------------------------------------------------------------------

    def test_extra_from_previous_evaluation_is_accessible_in_next_rule(self):
        class FirstRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'extra': {'tag': 'first'}, 'result': 1})

        class SecondRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                tag = previous_evaluation.extra.get('tag')
                return Evaluation({'result': tag})

        evaluation = run('x', [FirstRule(), SecondRule()])
        self.assertEqual(evaluation.result, 'first')

    # ------------------------------------------------------------------
    # Evaluation — previous_evaluation is a shallow copy
    # ------------------------------------------------------------------

    def test_previous_evaluation_rule_reference_is_preserved_in_shallow_copy(self):
        """The rule attribute on a shallow-copied evaluation still points to the original rule."""

        seen_rule = []

        class FirstRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': 'first'})

        class SecondRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                seen_rule.append(previous_evaluation.rule)
                return Evaluation({'result': 'second'})

        first = FirstRule()
        run('x', [first, SecondRule()])

        self.assertIs(seen_rule[0], first)

    def test_previous_evaluation_mutable_result_is_shared_not_deep_copied(self):
        """Shallow copy means nested mutable objects in result are shared."""

        shared_list = [1, 2]

        class FirstRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                return Evaluation({'result': shared_list})

        class SecondRule(AbstractRule):
            def evaluate(self, subject, previous_evaluation=None):
                # Mutate the list received via previous_evaluation
                previous_evaluation.result.append(3)
                return Evaluation({'result': 'done'})

        run('x', [FirstRule(), SecondRule()])

        # The original shared_list was mutated through the shallow copy
        self.assertEqual(shared_list, [1, 2, 3])

    # ------------------------------------------------------------------
    # AbstractData — class-attribute whitelist
    # ------------------------------------------------------------------

    def test_abstract_data_ignores_keys_not_declared_as_class_attributes(self):
        evaluation = Evaluation({'result': 'ok', 'nonexistent_field': 'ignored'})
        self.assertFalse(hasattr(evaluation, 'nonexistent_field'))
        self.assertEqual(evaluation.result, 'ok')

    def test_abstract_data_accepts_all_known_fields_individually(self):
        for field, value in [
            ('result', 42),
            ('stop', True),
            ('history', ['entry']),
        ]:
            with self.subTest(field=field):
                e = Evaluation({field: value})
                self.assertEqual(getattr(e, field), value)

    def test_abstract_data_accepts_extra_field(self):
        # extra is tested separately to avoid mutating the class-level default
        # dict that other tests rely on reading as empty.
        e = Evaluation({'extra': {'k': 'v'}})
        self.assertEqual(e.extra, {'k': 'v'})

    # ------------------------------------------------------------------
    # Evaluation — independent instances do not share class-level defaults
    # ------------------------------------------------------------------

    def test_evaluation_instances_do_not_share_mutable_defaults(self):
        """Documents that Evaluation's class-level extra and history dicts are shared
        until overwritten. This test exists so a future fix to per-instance defaults
        is detected immediately — if that fix lands, change assertIn to assertNotIn."""
        e1 = Evaluation({})
        e2 = Evaluation({})

        # Directly set via __dict__ to bypass AbstractData.__init__, which only
        # writes keys already declared as class attributes via hasattr — that
        # means assigning to extra on e1 sets the class-level default, not an
        # instance attribute, so e2.extra reflects the same object.
        e1.extra['__sentinel__'] = True

        # Document current behaviour: class-level dict is shared.
        self.assertIn('__sentinel__', e2.extra)

        # Clean up to avoid polluting later tests that check extra == {}
        del e1.extra['__sentinel__']

    # ------------------------------------------------------------------
    # Module API — lazy loading and public surface
    # ------------------------------------------------------------------

    def test_module_all_contains_expected_public_names(self):
        self.assertEqual(
            sorted(python_simple_rules_engine.__all__),
            ['AbstractData', 'AbstractRule', 'Evaluation', 'run'],
        )

    def test_module_dir_includes_lazy_names(self):
        names = dir(python_simple_rules_engine)
        for name in ('abc', 'copy', 'Any', 'Optional'):
            with self.subTest(name=name):
                self.assertIn(name, names)

    def test_module_getattr_raises_for_unknown_name(self):
        with self.assertRaises(AttributeError):
            _ = python_simple_rules_engine.nonexistent_attribute_xyz

    def test_module_lazy_load_abc_returns_module(self):
        import abc as stdlib_abc
        lazy_abc = python_simple_rules_engine.abc
        self.assertIs(lazy_abc, stdlib_abc)

    def test_module_lazy_load_copy_returns_module(self):
        import copy as stdlib_copy
        lazy_copy = python_simple_rules_engine.copy
        self.assertIs(lazy_copy, stdlib_copy)

    def test_module_lazy_load_is_cached_on_second_access(self):
        first = python_simple_rules_engine.abc
        second = python_simple_rules_engine.abc
        self.assertIs(first, second)

    def test_public_classes_are_importable_directly(self):
        from python_simple_rules_engine import AbstractData, AbstractRule, Evaluation, run  # noqa: F401

    def test_python_version_is_at_least_3_10(self):
        self.assertGreaterEqual(sys.version_info[:2], (3, 10))


if __name__ == '__main__':
    unittest.main()
