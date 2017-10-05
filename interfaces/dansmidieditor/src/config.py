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

	def prettied_sequence(self):
		if self.mode=='command':
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
		else: r=''.join(self.sequence)
		return r

	def command(self):
		command=self.prettied_sequence().split()
		name=command[0][1:]
		params=command[1:]
		if hasattr(self, name):
			getattr(self, name)(*params)
			self.reset()
		else:
			self.reset()
			self.view.text='no such command'

	def load(self, path): self.view.load(path)

	def mouse_motion (self, regex=r'.* x.*'                  , order=  1): self.sequence=self.sequence[:-1]
	def quit         (self, regex=r'.* q'                    , order=  2): self.done=True
	def reset        (self, regex=r'.* >Esc'                 , order=  3): self.sequence=[]; self.mode='normal'; self.show_sequence()
	def command_start(self, regex=r' <.Shift <;$'            , order=  4): self.mode='command'; self.show_sequence()
	def command_end  (self, regex=r' <.Shift <;.*>Return'    , order=  5): self.command()
	def backspace    (self, regex=r'.* <Backspace >Backspace', order=990):
		if self.mode=='command':
			for i in reversed(range(len(self.sequence)-2)):
				if self.sequence[i][0]=='<': break
			self.sequence=self.sequence[:i]
		else: self.sequence=self.sequence[:-3]
		self.show_sequence()
	def show_sequence(self, regex=r'.*'                      , order=999): self.view.text=self.prettied_sequence()

controls=Controls()
