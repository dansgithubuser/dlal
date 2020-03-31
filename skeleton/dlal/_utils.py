import os

DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(DIR))
ASSETS_DIR = os.path.join(REPO_DIR, 'assets')

def snake_to_upper_camel_case(s):
    return ''.join(i.capitalize() for i in s.split('_'))
