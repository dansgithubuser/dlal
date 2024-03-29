import dlal

import atexit

class Monitor(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(self,
            {
                'audio': ('audio', [], {'driver': True, 'run_size': 4096, 'mic': True}),
                'tape': ('tape', [], {'size': 1 << 16}),
                'stft': 'stft',
                'monitor': 'monitor',
            },
            name=name,
        )
        dlal.connect(
            [self.audio, '+>', self.tape],
            self.stft,
            self.monitor,
        )
    
    def start(self):
        self.audio.start()
        atexit.register(lambda: self.audio.stop())
