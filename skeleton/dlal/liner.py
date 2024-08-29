from ._component import Component

import midi

class Liner(Component):
    def __init__(self, midi_path=None, **kwargs):
        Component.__init__(self, 'liner', **kwargs)
        if midi_path:
            self.load(midi_path, immediate=True)

    def load(self, file_path, immediate=False):
        song = midi.Song(file_path)
        tempos = song.filterleave(lambda i: i.type() == 'tempo')
        for i in range(len(song.tracks)):
            deltamsgs = [
                {
                    'delta': i.delta,
                    'msg': i.bytes,
                }
                for i in midi.interleave(
                    song.tracks[i].filter(lambda i: i.type() != 'tempo'),
                    tempos,
                )
            ]
            self.command_immediate(
                'set_midi',
                [
                    i,
                    song.ticks_per_quarter,
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

    def split_notes(notes, sep_samples=100):
        latest_off = 0
        result = [[]]
        for note in notes:
            if note['on'] > latest_off + sep_samples and result[-1]:
                result.append([])
            result[-1].append(note)
            latest_off = max(note['off'], latest_off)
        return result
