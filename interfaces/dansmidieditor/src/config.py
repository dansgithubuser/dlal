from controls import AbstractControls
from view import View

configuration='''
mode .*
order -1
.* x.*: self.sequence=self.sequence[:-1]
.* (q|<.Ctrl <q): self.done=True
.* <Backspace >Backspace:
	if self.mode=='command':
		for i in reversed(range(len(self.sequence)-2)):
			if self.sequence[i][0]=='<': break
		self.sequence=self.sequence[:i]
	else: self.sequence=self.sequence[:-3]
 <Esc >Esc: self.reset()
.* <.Shift$: self.shift=True
.+ >.Shift$: self.shift=False
 >.Shift$: self.shift=False; self.clear()
order 0
.* >Esc: self.clear()

mode normal
order -2
 <Esc >Esc:       self.view.deselect(); self.clear()
order 0
.* >j:
	if self.shift: self.view.cursor_note_down(self.reps())
	else:          self.view.cursor_down     (self.reps())
	self.clear()
.* >k:
	if self.shift: self.view.cursor_note_up  (self.reps())
	else:          self.view.cursor_up       (self.reps())
	self.clear()
.* >l:            self.view.cursor_right    (self.reps()); self.clear()
.* >h:            self.view.cursor_left     (self.reps()); self.clear()
 <i >i$:          self.mode='insert'; self.clear()
 <Return >Return: self.view.select(); self.clear()
.* >Down:         self.view.transpose(-self.reps()); self.clear()
.* >Up:           self.view.transpose( self.reps()); self.clear()
.* >d:            self.view.set_duration(self.fraction()); self.clear()
 <Delete >Delete: self.view.delete(); self.clear()
.* >s: if self.shift: self.view.more_multistaffing(self.reps()); self.clear()
.* >x: if self.shift: self.view.less_multistaffing(self.reps()); self.clear()
 <.Shift <;$:     self.mode='command'; self.clear()

mode command
 .*>Return: self.command(); self.reset()

mode insert
 <z >z:         self.view.add_note( 0); self.clear()
 <s >s:         self.view.add_note( 1); self.clear()
 <x >x:         self.view.add_note( 2); self.clear()
 <d >d:         self.view.add_note( 3); self.clear()
 <c >c:         self.view.add_note( 4); self.clear()
 <v >v:         self.view.add_note( 5); self.clear()
 <g >g:         self.view.add_note( 6); self.clear()
 <b >b:         self.view.add_note( 7); self.clear()
 <h >h:         self.view.add_note( 8); self.clear()
 <n >n:         self.view.add_note( 9); self.clear()
 <j >j:         self.view.add_note(10); self.clear()
 <m >m:         self.view.add_note(11); self.clear()
 <Space >Space: self.view.skip_note( ); self.clear()
 .* >d:         self.view.set_duration(self.fraction(skip=1)); self.clear()
'''

class Controls(AbstractControls):
	def __init__(self):
		self.configure(configuration)
		AbstractControls.__init__(self)
		self.done=False
		self.view=View()
		self.shift=False

	def reps(self):
		try: return int(self.sequence_as_text()[:-1])
		except: return 1

	def fraction(self, skip=0):
		from fractions import Fraction
		try:
			s=self.sequence_as_text()[skip:]
			import re
			m=re.search('([0-9]+)/([0-9]+)', s)
			if m: return Fraction(*[int(i) for i in m.groups()])
			return Fraction(int(s[:-1]), 1)
		except: return Fraction(1)

	def command(self, command=None):
		if not command:
			command=self.sequence_as_text()
			command=command.split()
			name=command[0]
		else:
			command=command.split()
			name=command[0]
		params=command[1:]
		if hasattr(self, name): getattr(self, name)(*params)
		else: print('no such command "{}"'.format(name))

	def load(self, path): self.view.load(path)
	def pdb(self): import pdb; pdb.set_trace()

	def on_input(self):
		if   self.mode=='command': self.view.text=':'+self.sequence_as_text()
		elif self.mode=='insert' : self.view.text='i'+''.join(self.sequence)
		else                     : self.view.text=    ''.join(self.sequence)

controls=Controls()
