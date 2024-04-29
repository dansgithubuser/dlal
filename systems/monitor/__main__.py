#===== imports =====#
from system import MonitorSys

import dlal

import http.server
from pathlib import Path
import signal
import socketserver
import sys

#===== init =====#
monitor_sys = MonitorSys()

#===== helpers =====#
def sample(name):
    monitor_sys.monitor.sample(name)

def save(path='monitor.json'):
    monitor_sys.save(path)

def load(path='monitor.json'):
    monitor_sys.load(path)

def plot():
    import dansplotcore as dpc
    plot = dpc.Plot(primitive=dpc.p.Line())
    categories = monitor_sys.monitor.categories()
    for name, category in categories.items():
        plot.plot(category, legend=name)
    plot.show()

#===== run =====#
if Path('monitor.json').exists():
    load('monitor.json')
monitor_sys.start_all()
if not sys.flags.interactive:
    print('ctrl-c to quit.')
    signal.pause()
