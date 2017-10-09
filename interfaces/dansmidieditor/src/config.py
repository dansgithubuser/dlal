from controls import AbstractControls
from view import View

shift_table={
	'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F',
	'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L',
	'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R',
	's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X',
	'y': 'Y', 'z': 'Z',
	'1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
	'6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
	'[': '{', ']': '}', ';': ':', ',': '<', '.': '>',
	"'": '"', '/': '?', '`': '~', '=': '+', '-': '_',
	'\\': '|',
}

class Controls(AbstractControls):
	def __init__(self):
		AbstractControls.__init__(self)
		self.done=False
		self.view=View()
		self.mode='normal'

	def prettied_sequence(self, override_mode=None):
		if 'command' in [self.mode, override_mode]:
			shift=False
			r=''
			for i in self.sequence:
				c=i[1:]
				if   i[0]=='<':
					if c in shift_table: r+=shift_table[c] if shift else c
					elif c=='Space': r+=' '
					elif c[1:]=='Shift': shift=True#LShift or RShift
				elif i[0]=='>':
					if   c[1:]=='Shift': shift=False#LShift or RShift
				else: assert False
		elif 'insert' in [self.mode, override_mode]:
			r='i'+''.join(self.sequence[2:])
		else: r=''.join(self.sequence)
		return r

	def reps(self):
		try: return int(self.prettied_sequence('command')[:-1])
		except: return 1

	def fraction(self, skip=0):
		from fractions import Fraction
		try:
			s=self.prettied_sequence('command')[skip:]
			import re
			m=re.search('([0-9]+)/([0-9]+)', s)
			if m: return Fraction(*[int(i) for i in m.groups()])
			return Fraction(int(s[:-1]), 1)
		except: return Fraction(1)

	def command(self, command=None):
		if not command:
			command=self.prettied_sequence()
			command=command.split()
			name=command[0][1:]
		else:
			command=command.split()
			name=command[0]
		params=command[1:]
		if hasattr(self, name):
			getattr(self, name)(*params)
			self.reset()
		else:
			self.reset()
			self.view.text='no such command "{}"'.format(name)

	def load(self, path): self.view.load(path)
	def pdb(self): import pdb; pdb.set_trace()

	def mouse_motion (self, regex=r'.* x.*'                  , order=  0): self.sequence=self.sequence[:-1]
	def down         (self, regex=r'[^;i]* >j'               , order= 10): self.view.cursor_down     (self.reps()); self.reset()
	def up           (self, regex=r'[^;i]* >k'               , order= 11): self.view.cursor_up       (self.reps()); self.reset()
	def right        (self, regex=r'[^;i]* >l'               , order= 12): self.view.cursor_right    (self.reps()); self.reset()
	def left         (self, regex=r'[^;i]* >h'               , order= 13): self.view.cursor_left     (self.reps()); self.reset()
	def down_note    (self, regex=r'[^;i]* <.Shift.*>j'      , order= 14): self.view.cursor_note_down(self.reps()); self.reset()
	def up_note      (self, regex=r'[^;i]* <.Shift.*>k'      , order= 15): self.view.cursor_note_up  (self.reps()); self.reset()
	def insert       (self, regex=r' <i >i$'                 , order= 20): self.mode='insert'; self.show_sequence()
	def note_c       (self, regex=r' <i >i <z >z'            , order= 21): self.view.add_note( 0); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_cs      (self, regex=r' <i >i <s >s'            , order= 22): self.view.add_note( 1); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_d       (self, regex=r' <i >i <x >x'            , order= 23): self.view.add_note( 2); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_eb      (self, regex=r' <i >i <d >d'            , order= 24): self.view.add_note( 3); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_e       (self, regex=r' <i >i <c >c'            , order= 25): self.view.add_note( 4); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_f       (self, regex=r' <i >i <v >v'            , order= 26): self.view.add_note( 5); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_fs      (self, regex=r' <i >i <g >g'            , order= 27): self.view.add_note( 6); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_g       (self, regex=r' <i >i <b >b'            , order= 28): self.view.add_note( 7); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_ab      (self, regex=r' <i >i <h >h'            , order= 29): self.view.add_note( 8); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_a       (self, regex=r' <i >i <n >n'            , order= 30): self.view.add_note( 9); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_bb      (self, regex=r' <i >i <j >j'            , order= 31): self.view.add_note(10); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_b       (self, regex=r' <i >i <m >m'            , order= 32): self.view.add_note(11); self.sequence=self.sequence[:2]; self.show_sequence()
	def note_skip    (self, regex=r' <i >i <Space >Space'    , order= 33): self.view.skip_note( ); self.sequence=self.sequence[:2]; self.show_sequence()
	def select       (self, regex=r' <Return >Return'        , order= 40): self.view.select(); self.reset()
	def deselect     (self, regex=r' <Esc >Esc'              , order= 41): self.view.deselect(); self.reset()
	def note_down    (self, regex=r'[^;i]* >Down'            , order= 45): self.view.transpose(-self.reps()); self.reset()
	def note_up      (self, regex=r'[^;i]* >Up'              , order= 46): self.view.transpose( self.reps()); self.reset()
	def duration     (self, regex=r'[^;i]* >d'               , order= 50): self.view.set_duration(self.fraction(      )); self.reset()
	def duration_i   (self, regex=r' <i.* >d'                , order= 51): self.view.set_duration(self.fraction(skip=1)); self.sequence=self.sequence[:2]; self.show_sequence()
	def delete       (self, regex=r' <Delete >Delete'        , order= 60): self.view.delete(); self.reset()
	def quit         (self, regex=r'.* (q|<.Ctrl <q)'        , order=120): self.done=True
	def reset        (self, regex=r'.* >Esc'                 , order=130): self.sequence=[]; self.mode='normal'; self.show_sequence()
	def command_start(self, regex=r' <.Shift <;$'            , order=140): self.mode='command'; self.show_sequence()
	def command_end  (self, regex=r' <.Shift <;.*>Return'    , order=150): self.command()
	def backspace    (self, regex=r'.* <Backspace >Backspace', order=990):
		if self.mode=='command':
			for i in reversed(range(len(self.sequence)-2)):
				if self.sequence[i][0]=='<': break
			self.sequence=self.sequence[:i]
		else: self.sequence=self.sequence[:-3]
		self.show_sequence()
	def show_sequence(self, regex=r'.*'                      , order=999): self.view.text=self.prettied_sequence()

controls=Controls()
