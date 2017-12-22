track_header_size=8

def read_delta(bytes, i):
	'''Return (delta, i) where
delta is the delta ticks encoded starting from bytes[0] and
i is incremented by the length of the delta in bytes.'''
	result=0
	for i in range(i, i+4):
		result<<=7
		result+=bytes[i]&0x7f
		if not bytes[i]&0x80: break
	else: raise Exception('delta too big')
	return (result, i+1)

def write_delta(ticks):
	'Return the bytes that specify a delta equal to ticks.'
	result=[]
	for i in range(4):
		byte=ticks&0x7f
		ticks=ticks>>7
		result=[byte]+result
		if ticks==0:
			for i in range(len(result)-1): result[i]|=0x80
			return result
	else: raise Exception('delta too big')

def add_etter(instance, name, desired_type, further_check=None):
	def etter(self, value=None, add=None, sub=None):
		if sub is not None:
			if add is not None: raise Exception('value is being both added and subbed')
			add=-sub
		if add is not None:
			if value is not None: raise Exception('value is being both set and accumulated')
			value=getattr(self, '_'+name, value)+add
		if value is not None:
			if type(value)!=desired_type:
				raise Exception('tried setting {} {} to value of type {}'.format(desired_type, name, type(value)))
			if further_check:
				if not further_check(value):
					raise Exception('further check failed when setting {} to {}'.format(name, value))
			setattr(self, '_'+name, value)
		return getattr(self, '_'+name)
	from types import MethodType
	setattr(instance, name, MethodType(etter, instance))

class Pair:
	'The track unit: a delta and MIDI event pair.'
	def __init__(self, delta, event):
		add_etter(self, 'delta', int)
		add_etter(self, 'event', list, further_check=lambda v: all([type(i)==int for i in v]))
		self.delta(delta)
		self.event(event)

def get_pairs(track_chunk):
	'''Return the pairs in track_chunk in a list.
track_chunk is assumed to have come from a track chunk produced by chunkitize.'''
	pairs=[]
	i=track_header_size
	status=None
	while i<len(track_chunk):
		delta, i=read_delta(track_chunk, i)
		x=track_chunk[i]
		if x&0xf0: status=x; i+=1
		if status&0xf0 in [0x80,0x90,0xa0,0xb0,0xe0]:
			parameters=track_chunk[i:i+2]
			i+=2
		elif status&0xf0 in [0xc0,0xd0]:
			parameters=track_chunk[i:i+1]
			i+=1
		elif status&0xf0==0xf0:
			if status==0xff:
				l=2+track_chunk[i+1]
				parameters=track_chunk[i:i+l]
				i+=l
			else:
				parameters=[]
		pairs.append(Pair(delta, [status]+parameters))
	if pairs[-1].event()!=[0xff, 0x2f, 0x00]: raise Exception('invalid last command')
	return pairs

#return an unsigned integer from a big-endian string of bytes
def big_endian_to_unsigned(bytes):
	result=0
	for byte in bytes:
		result<<=8
		result+=byte
	return result

#return a list of lists of MIDI file bytes, separated into the header and tracks
def chunkitize(bytes):
	header_length=14
	header_title=[ord(i) for i in 'MThd']
	if len(bytes)<header_length: raise Exception('header too short')
	if bytes[0:len(header_title)]!=header_title: raise(Exception('bad header'))
	chunks=[bytes[0:header_length]]
	track_title=[ord(i) for i in 'MTrk']
	i=header_length
	global track_header_size
	while len(bytes)>=i+track_header_size:
		if bytes[i:i+len(track_title)]!=track_title: raise Exception('bad track header')
		track_size=big_endian_to_unsigned(bytes[i+4:i+8])
		if len(bytes)<i+track_header_size+track_size: raise Exception('track too long')
		chunks+=[bytes[i:i+track_header_size+track_size]]
		i+=track_header_size+track_size
	if i!=len(bytes): raise Exception('malformed tracks')
	if big_endian_to_unsigned(bytes[10:12])!=len(chunks)-1: raise Exception('bad size')
	return chunks

class Event:
	@staticmethod
	def make(event_type, ticks, *args):
		result=Event()
		add_etter(result, 'type', str)
		add_etter(result, 'ticks', int)
		result.type(event_type)
		result.ticks(ticks)
		if event_type=='ticks_per_quarter':
			add_etter(result, 'ticks_per_quarter', int)
			result.ticks_per_quarter(args[0])
		elif event_type=='tempo':
			add_etter(result, 'us_per_quarter', int)
			result.us_per_quarter(args[0])
		elif event_type=='time_sig':
			add_etter(result, 'top', int)
			add_etter(result, 'bottom', int)
			result.top(args[0])
			result.bottom(args[1])
		elif event_type=='key_sig':
			add_etter(result, 'sharps', int)
			add_etter(result, 'minor', int)
			result.sharps(args[0])
			result.minor(args[1])
		elif event_type=='note':
			add_etter(result, 'duration', int)
			add_etter(result, 'channel', int)
			add_etter(result, 'number', int)
			result.duration(args[0])
			result.channel(args[1])
			result.number(args[2])
		elif event_type=='note_on':
			add_etter(result, 'channel', int)
			add_etter(result, 'number', int)
			result.channel(args[0])
			result.number(args[1])
		elif event_type=='note_off':
			add_etter(result, 'channel', int)
			add_etter(result, 'number', int)
			result.channel(args[0])
			result.number(args[1])
		else: raise Exception('invalid type')
		return result

	def split_note(self):
		assert self._type=='note'
		return [
			Event.make('note_on' , self._ticks               , self._channel, self._number),
			Event.make('note_off', self._ticks+self._duration, self._channel, self._number)
		]

	def end_of_note(self):
		assert self._type=='note'
		return self._ticks+self._duration

	def __lt__(self, other):
		if self._ticks==other._ticks:
			if self._type=='note_off' and other._type=='note_on': return True
			if self._type=='note_on' and other._type=='note_off': return False
		return self._ticks<other._ticks

	def __repr__(self):
		attrs=[i for i in dir(self) if i in [
			'_ticks_per_quarter',
			'_us_per_quarter',
			'_top',
			'_bottom',
			'_sharps',
			'_minor',
			'_duration',
			'_channel',
			'_number'
		]]
		attrs=['{}: {}'.format(i[1:], getattr(self, i)) for i in attrs]
		return '{}({}; {})'.format(self._type, self._ticks, ', '.join(attrs))

#Parse MIDI bytes and return a song
def parse(bytes):
	chunks=chunkitize(bytes)
	ticks_per_quarter=big_endian_to_unsigned(chunks[0][12:14])
	if ticks_per_quarter==0: raise Exception('invalid ticks per quarter')
	if big_endian_to_unsigned(chunks[0][8:10])!=1: raise Exception('unhandled file type')
	track=[Event.make('ticks_per_quarter', 0, ticks_per_quarter)]
	if len(chunks)<2: return [track]
	song=[]
	pairs=get_pairs(chunks[1])
	ticks=0
	for pair in pairs:
		ticks+=pair.delta()
		if pair.event()[0]&0xf0==0xf0:
			if pair.event()[0]==0xff:
				if pair.event()[1]==0x51:
					track+=[Event.make('tempo', ticks, big_endian_to_unsigned(pair.event()[3:6]))]
				elif pair.event()[1]==0x58:
					track+=[Event.make('time_sig', ticks, pair.event()[3], 1<<pair.event()[4])]
				elif pair.event()[1]==0x59:
					sharps=pair.event()[3]
					if sharps&0x80: sharps=(sharps&0x7f)-0x80
					track+=[Event.make('key_sig', ticks, sharps, pair.event()[4])]
	song+=[track]
	for i in range(2, len(chunks)):
		ticks=0
		pairs=get_pairs(chunks[i])
		track=[]
		for i in range(len(pairs)):
			pair=pairs[i]
			ticks+=pair.delta()
			if pair.event()[0]&0xf0==0x90 and pair.event()[2]!=0:#Note on
				duration=0
				for j in pairs[i+1:]:
					duration+=j.delta()
					if j.event()[0]&0xf0==0x90 and j.event()[2]==0 or j.event()[0]&0xf0==0x80:#Note off
						if pair.event()[1]==j.event()[1]: break
				track+=[Event.make('note', ticks, duration, pair.event()[0]&0x0f, pair.event()[1])]
		song+=[track]
	return song

#Read a MIDI file and return a nicely constructed list that represents the song in the MIDI.
#The list is structured as follows:
#It is a list of tracks.
#The first track specifies things that correspond to all tracks.
#The other tracks specify things specific to themselves.
#Each track is a list of events.
def read(file_name):
	def to_int(x):
		if type(x)==str: return ord(x)
		return int(x)
	with open(file_name, 'rb') as file: bytes=[to_int(i) for i in file.read()]
	return parse(bytes)

def to_big_endian(x, size):
	return [(x>>((size-1-i)*8))&0xff for i in range(size)]

#Write a MIDI track to a file based on a list of bytes.
#The track header and end message are appended automatically, so they should not be included in bytes.
def write_track(file, bytes):
	#Some idiot midi players ignore the first delta, so start with an empty text event
	empty_text_event=[0, 0xff, 0x01, 0]
	if bytes[:4]!=empty_text_event: bytes=empty_text_event+bytes
	#
	bytes+=[1, 0xff, 0x2f, 0]
	track_header=[ord(i) for i in 'MTrk']+to_big_endian(len(bytes), 4)
	bytes=track_header+bytes
	file.write(bytearray(bytes))

def ilog2(x):
	result=-1
	while x!=0:
		x>>=1
		result+=1
	if result==-1: raise Exception('input outside domain')
	return result

#Write a MIDI file based on a nicely constructed list.
def write(file_name, song):
	file=open(file_name, 'wb')
	header=[ord(i) for i in 'MThd']+[0, 0, 0, 6, 0, 1]+to_big_endian(len(song), 2)+to_big_endian(ticks_per_quarter(song), 2)
	file.write(bytearray(header))
	bytes=[]
	last_ticks=0
	for event in song[0][1:]:
		bytes+=write_delta(event.ticks()-last_ticks)
		if event.type()=='tempo':
			bytes+=[0xff, 0x51, 0x03]
			bytes+=to_big_endian(event.us_per_quarter(), 3)
		elif event.type()=='time_sig':
			bytes+=[0xff, 0x58, 0x04]
			bytes+=[event.top(), ilog2(event.bottom()), 24, 8]
		elif event.type()=='key_sig':
			bytes+=[0xff, 0x59, 0x02]
			sharps=event.sharps()
			if sharps<0: sharps=0x100+sharps
			bytes+=[sharps, event.minor()]
		else: raise Exception('unhandled event type: {}'.format(event.type()))
		last_ticks=event.ticks()
	write_track(file, bytes)
	for track in song[1:]:
		notes=[]
		for event in track:
			if event.type()=='note': notes+=event.split_note()
		notes.sort()
		last_ticks=0
		for i in range(len(notes)):
			temp=notes[i].ticks()
			notes[i].ticks(sub=last_ticks)
			last_ticks=temp
		bytes=[]
		for note in notes:
			if note.type()=='note_on':
				bytes+=write_delta(note.ticks())
				bytes+=[0x90|note.channel()]
				bytes+=[note.number()]
				bytes+=[0x7f]
			elif note.type()=='note_off':
				bytes+=write_delta(note.ticks())
				bytes+=[0x80|note.channel()]
				bytes+=[note.number()]
				bytes+=[0]
		write_track(file, bytes)
	file.close()
	return

#=====helpers=====#
import bisect

def empty_midi(staves=1, ticks_per_quarter=360):
	return [[Event.make('ticks_per_quarter', 0, ticks_per_quarter)]]+[[] for i in range(staves)]

def ticks_per_quarter(midi):
	assert midi[0][0].type()=='ticks_per_quarter'
	return midi[0][0].ticks_per_quarter()

def add_event(track, event):
	assert isinstance(event, Event)
	bisect.insort(track, event)

def add_note(midi, track, ticks, duration, number, channel=None):
	if channel==None: channel=track-1
	add_event(midi[track], Event.make('note', ticks, duration, channel, number))

def previous_note(midi, track, ticks):
	event=Event()
	event._ticks=ticks
	index=bisect.bisect_left(midi[track], event)-1
	if index==-1: return
	note=midi[track][index]
	if note.ticks()>=ticks: return
	return midi, track, index

def remove_note(note):
	midi, track, index=note
	note=midi[track][index]
	del midi[track][index]
	return note

def transpose_note(note, amount):
	midi, track, index=note
	midi[track][index].number(add=amount)

def notes_in(midi, track, ticks, duration, number=None, generous=False, track_end=None):
	if track_end==None: track_end=track
	result=[]
	for t in range(track, track_end+1):
		for i, v in enumerate(midi[t]):
			if v.ticks()>=ticks+duration: break#note starts after window ends
			if v.type()!='note': continue
			if number and v.number()!=number: continue
			if generous:
				if v.ticks()+v.duration()<=ticks: continue#note ends before window starts
			else:
				if v.ticks()<ticks: continue#note starts before window starts
				if v.ticks()+v.duration()>ticks+duration: continue#note ends after window ends
			result.append((t, i))
	return result

def delete(midi, notes):
	notes=sorted(notes, key=lambda x: -x[1])
	for track, i in notes: del midi[track][i]

def transpose(midi, notes, amount):
	for track, i in notes: midi[track][i].number(add=amount)

def deserialize_bytes(serialized):
	return [int(i[:2], 16) for i in serialized.split()]
