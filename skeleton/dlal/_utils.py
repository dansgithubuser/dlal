from collections.abc import Iterable
import os

DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(DIR))
ASSETS_DIR = os.path.join(REPO_DIR, 'assets')
DEPS_DIR = os.path.join(REPO_DIR, 'deps')

def snake_to_upper_camel_case(s):
    return ''.join(i.capitalize() for i in s.split('_'))

def iterable(x):
    return isinstance(x, Iterable)
