from ._component import Component

import midi

class Liner(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'liner', name)

    def load(self, file_path, immediate=False):
        song = midi.Song().load(file_path)
        tempos = song.collect(['tempo'])
        for i in range(len(song.tracks())):
            deltamsgs = [
                {
                    'delta': i.delta(),
                    'msg': i.msg(),
                }
                for i in midi.interleave(
                    song.extract(i, ['note_on', 'note_off']),
                    tempos,
                )
            ]
            self.command_immediate(
                'load_midi',
                [
                    i,
                    song.ticks_per_quarter(),
                    deltamsgs,
                ],
                {
                    'immediate': immediate,
                },
            )

    def from_json(self, j):
        self.command('from_json', [j], do_json_prep=False)
