from collections.abc import Iterable
import os
import random
import re

DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(DIR))
ASSETS_DIR = os.path.join(REPO_DIR, 'assets')
DEPS_DIR = os.path.join(REPO_DIR, 'deps')

class NoContext:
    def __enter__(*args, **kwargs): pass
    def __exit__(*args, **kwargs): pass

def snake_to_upper_camel_case(s):
    return ''.join(i.capitalize() for i in s.split('_'))

def upper_camel_to_snake_case(s):
    return '_'.join(i.lower() for i in re.findall(r'[A-Z][a-z0-9_]*', s))

def iterable(x):
    return isinstance(x, Iterable)

def linear(a, b, t):
    return a * (1-t) + b * t

# minimize f(x')
# x' is a list of numbers from 0-1
# x is a starting guess
def minimize(f, x, heat=0.05, anneal=0.9, iterations=50):
    e = f(x)
    for i in range(iterations):
        for j in range(len(x)):
            x_n = [
                sorted([
                    0,
                    k + heat * (random.random() - 0.5),
                    1,
                ])[1]
                for k in x
            ]
            e_n = f(x_n)
            if e_n < e:
                x = x_n
                e = e_n
        heat *= anneal
    return x
