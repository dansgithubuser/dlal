from ._component import Component

import midi

class Liner(Component):
    def __init__(self, midi_path=None, **kwargs):
        Component.__init__(self, 'liner', **kwargs)
        if midi_path:
            self.load(midi_path)

    def load(self, file_path, immediate=False):
        song = midi.Song(file_path)
        tempos = song.filterleave(lambda i: i.type() == 'tempo')
        for i in range(len(song.tracks())):
            deltamsgs = [
                {
                    'delta': i.delta(),
                    'msg': i.msg(),
                }
                for i in midi.interleave(
                    song.tracks(i).filter(lambda i: i.type() in [
                        'note_on',
                        'note_off',
                        'control_change',
                        'pitch_wheel_change',
                    ]),
                    tempos,
                )
            ]
            self.command_immediate(
                'set_midi',
                [
                    i,
                    song.ticks_per_quarter(),
                    deltamsgs,
                ],
                {
                    'immediate': immediate,
                },
            )

    def get_midi_all(self):
        return self.command_immediate('get_midi_all')

    def from_json(self, j):
        self.command('from_json', [j])
