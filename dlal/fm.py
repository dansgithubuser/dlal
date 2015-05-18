from .skeleton import *
import Tkinter as tkinter
import itertools, pprint

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

class VgmSetting:
	def __init__(self, sample):
		self.commands={}
		self.channel_commands=[{} for x in range(6)]
		self.op_commands=[[{} for y in range(4)] for x in range(6)]

	def __repr__(self):
		return 'commands: {0}\nchannel_commands: {1}\nop_commands: {2}\n'.format(
			pprint.pformat(self.commands),
			pprint.pformat(self.channel_commands),
			pprint.pformat(self.op_commands)
		)

	def __sub__(self, other):
		def dict_sub(a, b):
			result={}
			for key, value in a.iteritems():
				if key in b.keys():
					if a[key]!=b[key]:
						result[key]={'+': a[key], '-': b[key]}
				else:
					result[key]={'+': a[key]}
			for key, value in b.iteritems():
				if key not in a.keys():
					result[key]={'-': b[key]}
			return result
		result=VgmSetting()
		result.commands=dict_sub(self.commands, other.commands)
		for i in range(len(result.channel_commands)):
			result.channel_commands[i]=dict_sub(self.channel_commands[i], other.channel_commands[i])
			for j in range(len(result.op_commands[i])):
				result.op_commands[i][j]=dict_sub(self.op_commands[i][j], other.op_commands[i][j])
		return result

	def set(self, command, value, channel=None, op=None):
		if op!=None: self.op_commands[channel][op][command]=value
		elif channel!=None: self.channel_commands[channel][command]=value
		else: self.commands[command]=value
		self.changed=True

	def get(self, channel):
		result={'channel': dict(self.commands.items()+self.channel_commands[channel].items())}
		result['ops']=[]
		for op_commands in self.op_commands[channel]: result['ops'].append(op_commands)
		return result

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
			self.set_range(0, 16, 0.5, 1, o.m)
			for i in o.i: self.set_range(0, 4, scale=i)
		self.set_default()

	def set_range(self, start=0, end=1, resolution=0.00001, exponent=1.0, scale=None):
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
			for i in o.i: i.set(0)
		self.oscillators[0].o.set(1)

	def get_vgm(self, vgm_file_name, samples, start_samples=0, setting=None):
		def le(bytes):#little endian
			result=0
			for i in range(len(bytes)): result|=bytes[i]<<(i*8)
			return result
		def bits(byte, least, most):
			result=0
			for i in range(least, most): result|=(byte&(1<<i))>>least
			return result
		def boolean(x, f='disable', t='enable'): return t if x else f
		def op_range(first_register, last_register):
			return [x for y in range(first_register, last_register, 4) for x in range(y, y+3)]
		def op_to_str(channel, op): return 'channel {0:d} op {1:d}'.format(channel, op)
		with open(vgm_file_name, 'rb') as vgm_file: vgm=[ord(x) for x in vgm_file.read()]
		if vgm[0:4]!=[ord(x) for x in 'Vgm ']: raise Exception('vgm: wrong file identification')
		if le(vgm[0x8:0xc])!=0x150: raise Exception('vgm: unhandled version')
		if samples==None: samples=le(vgm[0x18:0x1c])
		sample=start_samples
		if setting==None: setting=VgmSetting(sample)
		i=0x34+le(vgm[0x34:0x38])
		while i<len(vgm) and sample<=samples:
			if vgm[i] in [0x52, 0x53]:
				if sample<start_samples: continue
				port=boolean(vgm==0x53, 0, 1)
				if vgm[i+1] in op_range(0x30, 0xa0):
					op=(vgm[i+1]%16)/4
					channel=(vgm[i+1]-0x30)%4+boolean(port, 0, 3)
				if vgm[i+1]==0x22:
					fLut=[3.98, 5.56, 6.02, 6.37, 6.88, 9.63, 48.1, 72.2]
					setting.set('lfo', [boolean(bits(vgm[i+2], 3, 4)), fLut[bits(vgm[i+2], 0, 3)], 'Hz'])
				elif vgm[i+1]==0x26: pass#timer B
				elif vgm[i+1]==0x27:
					#ignore timer parts
					setting.set('special', bits(vgm[i+2], 6, 7), boolean(port, 3, 6))
				elif vgm[i+1]==0x28: pass#key on/off
				elif vgm[i+1]==0x2b:
					setting.set('dac', boolean(bits(vgm[i+2], 7, 8)))
				elif vgm[i+1] in op_range(0x30, 0x40):
					if bits(vgm[i+2], 4, 7):
						setting.set('detune', boolean(bits(vgm[i+2], 6, 7), 1, -1)*bits(vgm[i+2], 4, 6), channel, op)
					m=bits(vgm[i+2], 0, 4)
					if m==0: m=0.5
					setting.set('multiply', m, channel, op)
				elif vgm[i+1] in op_range(0x40, 0x50):
					setting.set('total level', bits(vgm[i+2], 0, 7), channel, op)
				elif vgm[i+1] in op_range(0x50, 0x60):
					setting.set('rate scaling', bits(vgm[i+2], 6, 8), channel, op)
					setting.set('attack rate', bits(vgm[i+2], 0, 5), channel, op)
				elif vgm[i+1] in op_range(0x60, 0x70):
					setting.set('first decay rate', bits(vgm[i+2], 0, 5), channel, op)
					setting.set('lfo amplitude modulation', bits(vgm[i+2], 7, 8), channel, op)
				elif vgm[i+1] in op_range(0x70, 0x80):
					setting.set('second decay rate', bits(vgm[i+2], 0, 5), channel, op)
				elif vgm[i+1] in op_range(0x80, 0x90):
					setting.set('second level', bits(vgm[i+2], 4, 8)*8, channel, op)
					setting.set('release rate', bits(vgm[i+2], 0, 4), channel, op)
				elif vgm[i+1] in op_range(0x90, 0xa0):
					if vgm[i+2]!=0: raise Exception('vgm: proprietary register not set to 0')
				elif vgm[i+1] in [0xa0, 0xa4, 0xa1, 0xa5]: pass#frequency of normal channels
				elif vgm[i+1] in [0xa2, 0xa8, 0xa9, 0xaa]:
					channel=boolean(port, 3, 6)
					op=[0xa2, 0xa8, 0xa9, 0xaa].index(vgm[i+1])
					setting.set('frequency lo', vgm[i+2], channel, op)
				elif vgm[i+1] in [0xa6, 0xac, 0xad, 0xae]:
					channel=boolean(port, 3, 6)
					op=[0xa6, 0xac, 0xad, 0xae].index(vgm[i+1])
					setting.set('frequency hi', bits(vgm[i+2], 0, 3), channel, op)
				elif vgm[i+1] in range(0xb0, 0xb3):
					channel=vgm[i+1]-0xb0+boolean(port, 0, 3)
					setting.set('feedback', bits(vgm[i+2], 3, 6), channel)
					setting.set('algorithm', bits(vgm[i+2], 0, 3), channel)
				elif vgm[i+1] in range(0xb4, 0xb7):
					channel=vgm[i+1]-0xb4+boolean(port, 0, 3)
					setting.set('stereo l', bits(vgm[i+2], 7, 8), channel)
					setting.set('stereo r', bits(vgm[i+2], 6, 7), channel)
					amsLut=[0, 1.4, 5.9, 11.8]
					setting.set('lfo amplitude modulation sensitivity', [amsLut[bits(vgm[i+2], 4, 6)], 'dB'], channel)
					fmsLut=[0, 3.4, 6.7, 10, 14, 20, 40, 80]
					setting.set('lfo frequency modulation sensitivity', [fmsLut[bits(vgm[i+2], 0, 3)], 'cents'], channel)
				else: raise Exception('vgm: unhandled register {0:x}'.format(vgm[i+1]))
				i+=3
			elif vgm[i]&0x70==0x70:
				sample+=bits(vgm[i], 0, 4)
				i+=1
			elif vgm[i]==0x61:
				sample+=le(vgm[i+1:i+2])
				i+=3
			elif vgm[i]==0x66: break
			else: raise Exception('vgm: unhandled command {0:x}'.format(vgm[i]))
		return setting

	def set_vgm(self, vgm, channel):
		for o in self.oscillators:
			self.set_range(exponent=1, scale=o.a)
			self.set_range(exponent=1, scale=o.d)
			self.set_range(exponent=1, scale=o.r)
		#defaults
		feedback=0.0
		algorithm=0
		total_level=[0.0]*4
		#algorithms
		algorithm_connections=[
			[[0, 1], [1, 2], [2, 3]],
			[[0, 2], [1, 2], [2, 3]],
			[[0, 3], [1, 2], [2, 3]],
			[[0, 1], [1, 3], [2, 3]],
			[[0, 1], [2, 3]],
			[[0, 1], [0, 2], [0, 3]],
			[[0, 1]],
			[]
		]
		algorithm_outputs=[
			[3],
			[3],
			[3],
			[3],
			[1, 3],
			[1, 2, 3],
			[1, 2, 3],
			[0, 1, 2, 3]
		]
		#extract parameters
		commands=vgm.get(channel)
		for command, value in commands['channel'].iteritems():
			if command=='feedback':
				if not value: feedback=0
				else: feedback=2.0**(value-9)
			elif command=='algorithm': algorithm=value
		for i in range(len(commands['ops'])):
			for command, value in commands['ops'][i].iteritems():
				if command=='multiply': self.oscillators[i].m.set(value)
				elif command=='total level': total_level[i]=2**(-value/32.0)
				elif command=='attack rate': self.oscillators[i].a.set(2**((value-1)/2.0)/(self.sample_rate*8));
				elif command=='first decay rate': self.oscillators[i].d.set(2**((value-1)/2.0)/(self.sample_rate*24))
				elif command=='second level': self.oscillators[i].s.set(1.0/2**value)
				elif command=='release rate': self.oscillators[i].r.set(2**value/(self.sample_rate*24.0))
		#clear connections and outputs
		for o in self.oscillators:
			o.o.set(0)
			for i in range(len(self.oscillators)): o.i[i].set(0)
		#set connections and outputs
		self.oscillators[0].i[0].set(4*total_level[0]*feedback)
		for i, o in algorithm_connections[algorithm]:
			self.oscillators[o].i[i].set(4*total_level[i])
		for output in algorithm_outputs[algorithm]:
			self.oscillators[output].o.set(total_level[output])

	def live_command(self, command):
		self.commander.command('queue 0 0 '+command)
