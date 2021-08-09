from python_simple_rules_engine import AbstractRule, Evaluation, run
from time import time

start = time()


class Rule(AbstractRule):
    def evaluate(self, subject, previous_evaluation: Evaluation = None) -> Evaluation:
        return Evaluation({'stop': False, 'result': ''})


try:
    from memory_profiler import profile

    lenght = 1000000
    rules = []

    for _ in range(lenght):
        rules.append(Rule())

    @profile
    def _run(rules):
        run('the subject', rules, with_history=False)

    evaluation = _run(rules)

except ModuleNotFoundError:
    print('memory_usage module not found')

finish = time()

print(f'Done in {finish - start} seconds')
