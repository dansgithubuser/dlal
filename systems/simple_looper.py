import dlal

class Looper:
	def __init__(self, tracks, sample_rate, log_2_samples_per_callback, period, beats):
		#create
		self.system=dlal.System()
		self.sfml=dlal.Component('sfml')
		self.commander=dlal.Component('commander')
		self.record_switches=[dlal.Component('switch') for i in range(tracks)]
		self.liners=[dlal.Liner() for i in range(tracks)]
		self.replay_switches=[dlal.Component('switch') for i in range(tracks)]
		self.play_switches=[dlal.Component('switch') for i in range(tracks)]
		self.fms=[dlal.Component('fm') for i in range(tracks)]
		self.audio=dlal.Component('audio')
		#connect
		for i in range(tracks):
			#record/replay
			self.record_switches[i].connect_input(self.sfml)
			self.liners[i].connect_input(self.record_switches[i])
			self.replay_switches[i].connect_input(self.liners[i])
			self.fms[i].connect_input(self.replay_switches[i])
			#play
			self.play_switches[i].connect_input(self.sfml)
			self.fms[i].connect_input(self.play_switches[i])
			#audio
			self.fms[i].connect_output(self.audio)
			#commander
			self.commander.connect_output(self.play_switches[i])
			self.commander.connect_output(self.record_switches[i])
			self.commander.connect_output(self.replay_switches[i])
		#command
		self.liners[0].line('S %d %s'%(period/beats/2, 'z . '*beats))
		self.play_switches[0].command('set 0')
		self.commander.command('period %d'%period)
		for liner in self.liners: liner.command('period %d'%period)
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
	
	def play(self, track):
		for i in range(len(self.tracks)):
			self.commander.command('queue %d unset'%(i*3))
		self.commander.command('queue %d set 0'%(i*3))
	
	def record(self, track):
		for i in range(len(self.tracks)):
			self.commander.command('queue %d unset'%(i*3+1))
		self.commander.command('queue %d set 0'%(i*3+1))
	
	def replay(self, tracks):
		for i in range(len(self.tracks)):
			self.commander.command('queue %d %s'%(i*3+2, 'set 0' if i in tracks else 'unset'))

if __name__=='__main__':
	looper=Looper(4, 44100, 6, 6*64000, 16)
