import dlal

import atexit
from datetime import datetime
import pprint
import time

def timestamp():
    return datetime.now().astimezone().isoformat(' ', 'seconds')

class MonitorSys(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(self,
            {
                'audio': ('audio', [], {'driver': True, 'run_size': 4096, 'mic': True}),
                'afw': ('afw', [], {'context_duration': 5}),
                'stft': 'stft',
                'monitor': (
                    'monitor',
                    [],
                    {
                        'format': (
                            'write_start',
                            ['%.flac', 5],
                            {},
                        ),
                        'known_category_cmd_rate': 0.01,
                    },
                ),
            },
            name=name,
        )
        dlal.connect(
            [self.audio, '+>', self.afw],
            self.stft,
            [self.monitor, '+>', self.afw],
        )

    def start(self):
        self.audio.start()
        atexit.register(lambda: self.audio.stop())

    def print_category_changes(self):
        category = None
        while True:
            cat = self.monitor.category_detected()
            if category != cat:
                category = cat
                print(timestamp(), category)
            time.sleep(1)

    def print_category_distances(self):
        while True:
            pprint.pprint(self.monitor.category_distances())
            time.sleep(1)
