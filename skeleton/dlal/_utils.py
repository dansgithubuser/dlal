from collections.abc import Iterable
import json
import os
from pathlib import Path
import random
import re
import socket

DIR = Path(__file__).resolve().parent
REPO_DIR = DIR.parent.parent
ASSETS_DIR = REPO_DIR / 'assets'
DEPS_DIR = REPO_DIR / 'deps'

class NoContext:
    def __enter__(*args, **kwargs): pass
    def __exit__(*args, **kwargs): pass

class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return str(o)

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
def minimize(f, x, heat=0.05, anneal=0.8, iterations=10):
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

def network_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for host in ['8.8.8.8', '0.0.0.0']:
        try:
            s.connect((host, 80))
        except OSError as e:
            if e.errno != 101 or host == '0.0.0.0': raise
    ip = s.getsockname()[0]
    s.close()
    return ip
