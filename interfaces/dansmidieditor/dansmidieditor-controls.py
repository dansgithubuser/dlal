controls=[
	('.* x.*', 'self.sequence=self.sequence[:-1]'),
	('.* -esc', 'self.sequence=[]'),
	('.* q', 'import sys; sys.exit()'),
	('.*', '''print(''.join([' '+i for i in self.sequence]))'''),
]
