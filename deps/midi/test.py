import midi

x=midi.read('trans.mid')
midi.write('trans2.mid', x)
with open('trans.mid', 'rb') as a:
	with open('trans2.mid', 'rb') as b:
		x=a.read()
		y=b.read()
		if x!=y:
			print(x)
			print(y)
			raise Exception()
