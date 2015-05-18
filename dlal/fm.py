from .skeleton import *
import Tkinter as tkinter
import itertools

class Oscillator:
	def __init__(self, i, oscillators, fm):
		self.fm=fm
		column=itertools.count()
		self.label=tkinter.Label(text=str(i)).grid(row=i, column=column.next())
		self.a=tkinter.Scale(command=lambda x: fm.live_command('a {0:d} {1:f}'.format(i, self.a.get()**self.exponents[self.a])))
		self.a.grid(row=i, column=column.next())
		self.d=tkinter.Scale(command=lambda x: fm.live_command('d {0:d} {1:f}'.format(i, self.d.get()**self.exponents[self.d])))
		self.d.grid(row=i, column=column.next())
		self.s=tkinter.Scale(command=lambda x: fm.live_command('s {0:d} {1:f}'.format(i, self.s.get()**self.exponents[self.s])))
		self.s.grid(row=i, column=column.next())
		self.r=tkinter.Scale(command=lambda x: fm.live_command('r {0:d} {1:f}'.format(i, self.r.get()**self.exponents[self.r])))
		self.r.grid(row=i, column=column.next())
		self.m=tkinter.Scale(command=lambda x:(
			fm.live_command('m {0:d} {1:f}'.format(i, self.m.get()**self.exponents[self.m])),
			fm.live_command('rate {0:d}'.format(fm.sample_rate))
		))
		self.m.grid(row=i, column=column.next())
		self.o=tkinter.Scale(command=lambda x: fm.live_command('o {0:d} {1:f}'.format(i, self.o.get()**self.exponents[self.o])))
		self.o.grid(row=i, column=column.next())
		self.i=[None]*oscillators
		for j in range(oscillators):
			def command(oscillator):
				return lambda x: fm.live_command(
					'i {0:d} {1:d} {2:f}'.format(
						i, oscillator, self.i[oscillator].get()**self.exponents[self.i[j]]
					)
				)
			self.i[j]=tkinter.Scale(command=command(j))
			self.i[j].grid(row=i, column=column.next())
		self.exponents={}
		for scale in self.scales(): self.exponents[scale]=1.0

	def scales(self):
		return filter(lambda x: isinstance(x, tkinter.Scale), vars(self).values())+self.i

	def set_exponent(self, scale, exponent):
		if scale in self.exponents: self.exponents[scale]=exponent

class Fm(Component):
	def __init__(self, sample_rate):
		Component.__init__(self, 'fm')
		self.command('rate {0:d}'.format(sample_rate))
		self.commander=Component('commander')
		self.commander.connect_output(self)
		self.sample_rate=sample_rate

	def add(self, system):
		self.commander.add(system)
		Component.add(self, system)

	def show_controls(self, title='dlal fm controls'):
		self.root=tkinter.Tk()
		self.root.title(title)
		oscillators=4
		column=itertools.count(1)
		self.oscillators=[Oscillator(i, oscillators, self) for i in range(oscillators)]
		self.a=tkinter.Label(text='a').grid(row=oscillators, column=column.next())
		self.d=tkinter.Label(text='d').grid(row=oscillators, column=column.next())
		self.s=tkinter.Label(text='s').grid(row=oscillators, column=column.next())
		self.r=tkinter.Label(text='r').grid(row=oscillators, column=column.next())
		self.o=tkinter.Label(text='m').grid(row=oscillators, column=column.next())
		self.o=tkinter.Label(text='o').grid(row=oscillators, column=column.next())
		self.i=[None]*oscillators
		for j in range(oscillators):
			self.i=tkinter.Label(text='i'+str(j)).grid(row=oscillators, column=column.next())
		self.set_range()
		for o in self.oscillators:
			self.set_range(exponent=4, scale=o.a)
			self.set_range(exponent=4, scale=o.d)
			self.set_range(exponent=4, scale=o.r)
			self.set_range(0, 16, 1, 1, o.m)
		self.set_default()

	def set_range(self, start=0, end=1, resolution=0.01, exponent=1.0, scale=None):
		if scale: scales=[scale]
		else: scales=[s for o in self.oscillators for s in o.scales()]
		for s in scales:
			s.config(from_=end, to=start, resolution=resolution)
			for o in self.oscillators: o.set_exponent(s, exponent)

	def set_default(self):
		for o in self.oscillators:
			o.a.set(0.3)
			o.d.set(0.3)
			o.s.set(1.0)
			o.r.set(0.3)
			o.m.set(1)
			o.o.set(0)
			for i in range(len(self.oscillators)): o.i[i].set(0)
		self.oscillators[0].o.set(1)

	def live_command(self, command):
		self.commander.command('queue 0 0 '+command)
