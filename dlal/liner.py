from .skeleton import *
from .qweboard import qwe_to_note

class Liner(Component):
    @staticmethod
    def from_dict(d, component_map): return Liner(from_dict=(d, component_map))

    def to_dict(self):
        d = {'component': self.to_str()}
        if hasattr(self, 'samples_per_quarter'):
            d['samples_per_quarter'] = self.samples_per_quarter
        return d

    def __init__(self, period_in_samples=0, samples_per_quarter=22050, from_dict=None, **kwargs):
        if from_dict:
            d, component_map = from_dict
            Component.__init__(self, 'liner', component=component_map[d['component']].transfer_component())
            if 'samples_per_quarter' in d:
                self.samples_per_quarter = d['samples_per_quarter']
            self.period_in_samples = int(self.periodic_get().split()[0])
            self.periodic_set_phase(0)
            return
        Component.__init__(self, 'liner', **kwargs)
        if period_in_samples:
            self.periodic_resize(period_in_samples)
            self.period_in_samples = period_in_samples
        if samples_per_quarter:
            self.samples_per_quarter = samples_per_quarter

    def line(self, text, immediate=False):
        stride = self.samples_per_quarter
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
        self.load(file_name, self.samples_per_quarter)
