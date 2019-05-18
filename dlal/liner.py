from .skeleton import *
from .qweboard import qwe_to_note

class Liner(Component):
    def __init__(self, period_in_samples=0, samples_per_quarter=0, **kwargs):
        Component.__init__(self, 'liner', **kwargs)
        if period_in_samples:
            self.periodic_resize(period_in_samples)
        if samples_per_quarter:
            self.command('samples_per_quarter', samples_per_quarter, immediate=True)

    def line(self, text, immediate=False):
        stride = self.samples_per_quarter(immediate=True)
        octave = 5
        sample = 0
        text = text.split()
        i = 0
        while i < len(text):
            t = text[i]
            i += 1
            if t == 'S':
                stride = int(text[i])
                i += 1
            elif t == 'O':
                octave = int(text[i])
                i += 1
            else:
                notes = []
                nextSample = sample+stride
                for j in range(len(t)):
                    if t[j] == '.':
                        if j != 0:
                            nextSample += stride
                    else:
                        notes.append(12 * octave + qwe_to_note[t[j]])
                for note in notes:
                    self.midi_event(sample, 0x90, note, 0x40, immediate=immediate)
                    self.midi_event(nextSample, 0x80, note, 0x40, immediate=immediate)
                sample = nextSample

    def edit(self):
        file_name = '.liner.tmp.mid'
        self.save(file_name)
        editor = os.path.join(root, 'deps', 'dansmidieditor', 'src', 'dansmidieditor.py')
        invoke('{} --command "edit {}"'.format(editor, file_name))
        self.load(file_name)
