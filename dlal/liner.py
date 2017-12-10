from .skeleton import *

g_notes={
	'z': 0, 's': 1, 'x': 2, 'd': 3, 'c': 4, 'v': 5,
	'g': 6, 'b': 7, 'h': 8, 'n': 9, 'j': 10, 'm': 11, ',': 12,
	'w': 12, '3': 13, 'e': 14, '4': 15, 'r': 16, 't': 17,
	'6': 18, 'y': 19, '7': 20, 'u': 21, '8': 22, 'i': 23, 'o': 24
}

class Liner(Component):
	@staticmethod
	def from_dict(d, component_map): return Liner(from_dict=(d, component_map))

	def to_dict(self):
		d={'component': self.to_str()}
		if hasattr(self, 'samples_per_quarter'): d['samples_per_quarter']=self.samples_per_quarter
		return d

	def __init__(self, period_in_samples=0, samples_per_quarter=22050, from_dict=None, **kwargs):
		if from_dict:
			d, component_map=from_dict
			Component.__init__(self, 'liner', component=component_map[d['component']].transfer_component())
			if 'samples_per_quarter' in d: self.samples_per_quarter=d['samples_per_quarter']
			self.period_in_samples=int(self.periodic_get().split()[0])
			self.periodic_set_phase(0)
			return
		Component.__init__(self, 'liner', **kwargs)
		if period_in_samples:
			self.periodic_resize(period_in_samples)
			self.period_in_samples=period_in_samples
		if samples_per_quarter: self.samples_per_quarter=samples_per_quarter

	def line(self, text):
		stride=self.samples_per_quarter
		octave=5
		sample=0
		text=text.split()
		i=0
		while i<len(text):
			t=text[i]
			i+=1
			if   t=='S': stride=int(text[i]); i+=1
			elif t=='O': octave=int(text[i]); i+=1
			else:
				notes=[]
				nextSample=sample+stride
				for j in range(len(t)):
					if t[j]=='.':
						if j!=0:
							nextSample+=stride
					else: notes.append(12*octave+g_notes[t[j]])
				for note in notes:
					self.midi_event(sample    , 0x90, note, 0x40)
					self.midi_event(nextSample, 0x80, note, 0x40)
				sample=nextSample

	def edit(self):
		file_name='.liner.tmp.mid'
		self.save(file_name, self.samples_per_quarter)
		editor=os.path.join(root, 'interfaces', 'dansmidieditor', 'src', 'dansmidieditor.py')
		invoke('{} --command "edit {}"'.format(editor, file_name))
		self.load(file_name, self.samples_per_quarter)
