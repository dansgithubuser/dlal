import dlal

class Looper:
	def __init__(self, tracks, sample_rate, log_2_samples_per_callback, period, bars, beats_per_bar):
		if tracks<2: raise Exception('there must be at least 2 tracks')
		self._commander_play_switch=0
		self._commander_record_switch=1
		self._commander_liner=2
		self._commander_fm=3
		self._commander_stride=4
		#create
		self.system=dlal.System()
		self.sfml=dlal.Component('sfml')
		self.commander=dlal.Component('commander')
		self.play_switches=[dlal.Component('switch') for i in range(tracks)]
		self.record_switches=[dlal.Component('switch') for i in range(tracks)]
		self.liners=[dlal.Liner() for i in range(tracks)]
		self.fms=[dlal.Component('fm') for i in range(tracks)]
		self.audio=dlal.Component('audio')
		#connect
		for i in range(tracks):
			self.commander.connect_output(self.play_switches[i])
			self.commander.connect_output(self.record_switches[i])
			self.commander.connect_output(self.liners[i])
			self.commander.connect_output(self.fms[i])
			self.play_switches[i].connect_input(self.sfml)
			self.record_switches[i].connect_input(self.sfml)
			self.liners[i].connect_input(self.record_switches[i])
			self.play_switches[i].connect_input(self.liners[i])
			self.fms[i].connect_input(self.play_switches[i])
			self.fms[i].connect_output(self.audio)
		#command
		self.commander.command('period %d'%period)
		for liner in self.liners: liner.command('period %d'%period)
		self.play_switches[0].command('set 0')
		line=[]
		for i in range(bars*beats_per_bar*2):
			halfbeat=i%2
			beat=i//2%beats_per_bar
			bar=i//2//beats_per_bar
			line.append('.')
			if halfbeat==0:
				if beat in [0, 1]: line[-1]='z'
			else:
				if bar&(1<<beat): line[-1]='z'
		line=' '.join(line)
		self.liners[1].line('S %d %s'%(period//(bars*beats_per_bar*2), line))
		self.play_switches[1].command('set 1')
		self.fms[1].command('d 0 {0:f}'.format(4.0/sample_rate))
		self.fms[1].command('s 0 0')
		self.fms[1].command('i 0 0 1')
		self.fms[1].command('i 0 1 1')
		self.fms[1].command('i 1 0 1')
		self.fms[1].command('i 1 1 1')
		for fm in self.fms: fm.command('rate %d'%sample_rate)
		self.audio.command('set %d %d'%(sample_rate, log_2_samples_per_callback))
		#add
		self.commander.add(self.system)
		self.sfml.add(self.system)
		for liner in self.liners: liner.add(self.system)
		self.audio.add(self.system)
		for fm in self.fms: fm.add(self.system)
		#start
		self.audio.command('start')
	
	def __del__(self):
		self.audio.command('finish')
	
	def _commander_index(self, index, output):
		return index*self._commander_stride+output
	
	def play(self, start, stop=[], delay=0):
		for i in stop:
			self.commander.command('queue %d %d unset'%(delay, self._commander_index(i, self._commander_play_switch)))
		for i in start:
			self.commander.command('queue %d %d set 0'%(delay, self._commander_index(i, self._commander_play_switch)))
	
	def record(self, start, stop=[], delay=0):
		for i in stop:
			self.commander.command('queue %d %d unset'%(delay, self._commander_index(i, self._commander_record_switch)))
		for i in start:
			self.commander.command('queue %d %d set 0'%(delay, self._commander_index(i, self._commander_record_switch)))

	def replay(self, start, stop=[], delay=1):
		for i in stop:
			self.commander.command('queue %d %d unset'%(delay, self._commander_index(i, self._commander_play_switch)))
		for i in start:
			self.commander.command('queue %d %d set 1'%(delay, self._commander_index(i, self._commander_play_switch)))

	def clear(self, tracks, delay=1):
		for i in tracks:
			self.commander.command('queue %d %d clear'%(delay, self._commander_index(i, self._commander_liner)))

if __name__=='__main__':
	looper=Looper(4, 44100, 6, 6*65536, 4, 4)
