import copy, os, sys
from fractions import Fraction

home=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(home, '..', '..', '..', 'deps', 'midi'))
import midi

us_per_minute=60.0*1000**2

class Cursor:
	def __init__(self, ticks_per_quarter):
		self.staff=0
		self.note=60
		self.ticks=Fraction(0)
		self.duration=Fraction(ticks_per_quarter)
		self.duty=Fraction(1)

	def coincide_note(self, note):
		self.ticks=Fraction(note.ticks())
		self.duration=Fraction(note.duration())

class View:
	def __init__(self, margin=6, text_size=12):
		self.midi=[[], []]
		self.ticks_per_quarter=256
		self.text=''
		self.margin=margin
		self.text_size=text_size
		self.staff=0
		self.staves=4.0
		self.multistaffing=1
		self.ticks=0
		self.duration=5760
		self.cursor=Cursor(self.ticks_per_quarter)
		self.deselect()
		self.unyank()
		self.visual=Cursor(0)
		self.visual.active=False
		self.unwritten=False
		self.banner_h=40
		#colors
		self.color_background=[  0,   0,   0]
		self.color_staves    =[  0,  32,   0, 128]
		self.color_c_line    =[ 16,  16,  16, 128]
		self.color_quarter   =[  8,   8,   8]
		self.color_notes     =[  0, 128, 128]
		self.color_other     =[  0, 128,   0]
		self.color_cursor    =[128,   0, 128, 128]
		self.color_visual    =[255, 255, 255,  64]
		self.color_selected  =[255, 255, 255]
		self.color_warning   =[255,   0,   0]

	#persistence
	def read(self, path):
		self.midi=midi.read(path)
		if len(self.midi)==1: self.midi.append([])
		self.ticks_per_quarter=midi.ticks_per_quarter(self.midi)
		self.cursor.duration=Fraction(self.ticks_per_quarter)
		self.cursor_down(0)
		self.unwritten=False
		self.path=path

	def write(self, path=None):
		if not path: path=self.path
		midi.write(path, self.midi)
		self.unwritten=False

	#cursor
	def cursor_down(self, amount):
		self.cursor.staff+=amount
		self.cursor.staff=max(self.cursor.staff, 0)
		self.cursor.staff=min(self.cursor.staff, len(self.midi)-2)
		#move up if cursor is above window
		self.staff=min(self.staff, self.cursor.staff)
		#move down if cursor is below window
		bottom=self.staff+int(self.staves)-1
		if self.cursor.staff>bottom: self.staff+=self.cursor.staff-bottom
		#figure cursor octave
		self.cursor.note%=12
		self.cursor.note+=self.calculate_octave(self.cursor.staff)*12

	def cursor_up(self, amount): self.cursor_down(-amount)

	def cursor_right(self, amount):
		self.cursor.ticks+=self.cursor.duration*amount
		self.cursor.ticks=max(Fraction(0), self.cursor.ticks)
		#move left if cursor is left of window
		self.ticks=min(self.ticks, int(self.cursor.ticks))
		#move right if cursor is right of window
		right=self.ticks+self.duration
		cursor_right=self.cursor.ticks+self.cursor.duration
		if cursor_right>right: self.ticks+=int(cursor_right)-right
		#figure cursor octave
		self.cursor.note%=12
		self.cursor.note+=self.calculate_octave(self.cursor.staff)*12

	def cursor_left(self, amount): self.cursor_right(-amount)

	def cursor_note_down(self, amount):
		self.cursor.note-=amount
		self.cursor.note=max(0, self.cursor.note)
		self.cursor.note=min(127, self.cursor.note)

	def cursor_note_up(self, amount): self.cursor_note_down(-amount)

	def set_duration(self, fraction_of_quarter):
		self.cursor.duration=Fraction(self.ticks_per_quarter)*fraction_of_quarter

	#window
	def more_multistaffing(self, amount):
		self.multistaffing+=amount
		self.multistaffing=max(1, self.multistaffing)
		self.multistaffing=min(6, self.multistaffing)

	def less_multistaffing(self, amount): self.more_multistaffing(-amount)

	#notes
	def add_note(self, number, advance=True):
		octave=self.calculate_octave(self.cursor.staff)
		midi.add_note(
			self.midi,
			self.cursor.staff+1,
			int(self.cursor.ticks),
			int(self.cursor.duration*self.cursor.duty),
			number+12*octave
		)
		if advance: self.skip_note()
		self.unwritten=True

	def previous_note(self):
		return midi.previous_note(self.midi, self.cursor.staff+1, int(self.cursor.ticks))

	def remove_note(self, note):
		if note==None: return
		return midi.remove_note(note)

	def transpose_note(self, note, amount):
		if note==None: return
		midi.transpose_note(note, amount)

	def skip_note(self):
		self.cursor.ticks+=self.cursor.duration

	#other midi events
	def add_tempo(self, quarters_per_minute):
		us_per_quarter=us_per_minute/quarters_per_minute
		midi.add_event(
			self.midi[0],
			midi.Event.make('tempo', int(self.cursor.ticks), int(us_per_quarter)),
		)

	#selection
	def select(self):
		args=[
			self.midi,
			self.cursor.staff+1,
			self.cursor.ticks,
			self.cursor.duration,
		]
		notes=midi.notes_in(*args, number=self.cursor.note)
		if not notes: notes=midi.notes_in(*args, number=self.cursor.note, generous=True)
		if not notes: notes=midi.notes_in(*args)
		if not notes: notes=midi.notes_in(*args, generous=True)
		for i in notes: self.selected.add(i)

	def deselect(self): self.selected=set()

	def is_selected(self, note):
		return any([self.midi[i[0]][i[1]]==note for i in self.selected])

	def delete(self):
		midi.delete(self.midi, self.selected)
		self.selected=set()
		self.unwritten=True

	def transpose(self, amount):
		midi.transpose(self.midi, self.selected, amount)
		self.unwritten=True

	def get_visual_duration(self):
		ticks=sorted([
			self.visual.ticks, self.visual.ticks+self.visual.duration,
			self.cursor.ticks, self.cursor.ticks+self.cursor.duration,
		])
		return ticks[0], ticks[-1]

	def toggle_visual(self):
		if self.visual.active:
			start, finish=self.get_visual_duration()
			notes=midi.notes_in(
				self.midi,
				track=min(self.visual.staff, self.cursor.staff)+1,
				ticks=start,
				duration=finish-start,
				track_end=max(self.visual.staff, self.cursor.staff)+1,
			)
			for i in notes: self.selected.add(i)
			self.visual.duration=finish-start
			self.visual.active=False
		else:
			self.visual=copy.deepcopy(self.cursor)
			self.visual.active=True

	def select(self):
		args=[
			self.midi,
			self.cursor.staff+1,
			self.cursor.ticks,
			self.cursor.duration,
		]
		notes=midi.notes_in(*args, number=self.cursor.note)
		if not notes: notes=midi.notes_in(*args, number=self.cursor.note, generous=True)
		if not notes: notes=midi.notes_in(*args)
		if not notes: notes=midi.notes_in(*args, generous=True)
		for i in notes: self.selected.add(i)

	def yank(self):
		if self.visual.active: self.toggle_visual()
		self.yanked=self.selected
		self.deselect()

	def unyank(self): self.yanked=set()

	def put(self):
		if not self.yanked: return
		notes=list(self.yanked)
		start=min([self.midi[track][index].ticks() for track, index in notes])
		for track, index in notes:
			note=self.midi[track][index]
			midi.add_note(
				self.midi,
				self.cursor.staff+1,
				int(self.cursor.ticks-start+note.ticks()),
				note.duration(),
				note.number(),
				note.channel(),
			)
		self.cursor.ticks+=self.visual.duration

	def info(self):
		for track, index in sorted(list(self.selected)): print(self.midi[track][index])

	#drawing
	def staves_to_draw(self):
		return range(self.staff, self.staff+min(int(self.staves)+1, len(self.midi)-1-self.staff))

	def notes_per_staff(self):
		return 24*self.multistaffing

	def h_staves(self):
		return self.h_window-self.banner_h

	def h_note(self):
		return self.h_staves()//self.staves//self.notes_per_staff()

	def y_note(self, staff, note, octave=0):
		y_staff=(staff+1-self.staff)*self.h_staves()//self.staves
		return int(self.banner_h+y_staff-(note+1-12*octave)*self.h_note())

	def x_ticks(self, ticks):
		return (ticks-self.ticks)*self.w_window//self.duration

	def endures(self, ticks):
		return ticks<self.ticks+self.duration

	def calculate_octave(self, staff):
		octave=5
		lo=60
		hi=60
		for i in self.midi[1+staff]:
			if i.type()!='note': continue
			if i.ticks()+i.duration()<self.ticks: continue
			if not self.endures(i.ticks()): break
			lo=min(lo, i.number())
			hi=max(hi, i.number())
		top=(octave+2)*12
		if hi>top: octave+=(hi-top+11)//12
		bottom=octave*12
		if lo<bottom: octave+=(lo-bottom)//12
		return octave

	def notate_octave(self, octave):
		octave-=5
		if octave>= 1: return '{}va'.format(1+7*octave)
		if octave<=-1: return '{}vb'.format(1-7*octave)
		return '-'

	def draw(self, media):
		media.clear(color=self.color_background)
		self.w_window=media.width()
		self.h_window=media.height()
		#quarters
		tph=2*self.ticks_per_quarter
		for i in range(self.duration//tph+2):
			media.fill(
				xi=self.x_ticks((self.ticks//tph+i)*tph),
				xf=self.x_ticks((self.ticks//tph+i)*tph+self.ticks_per_quarter),
				yi=0,
				yf=self.h_window,
				color=self.color_quarter
			)
		media.draw_vertices()
		#staves
		h=int(self.h_note())
		for m in range(self.multistaffing):
			for i in self.staves_to_draw():
				media.fill(xi=0, xf=self.w_window, y=self.y_note(i, 24*m), h=h, color=self.color_c_line)
				for j in [4, 7, 11, 14, 17]:
					media.fill(xi=0, xf=self.w_window, y=self.y_note(i, j+24*m), h=h, color=self.color_staves)
		media.draw_vertices()
		#octaves
		octaves={}
		for i in self.staves_to_draw():
			octaves[i]=self.calculate_octave(i)
			media.text(
				self.notate_octave(octaves[i]),
				x=self.margin,
				y=self.y_note(i, 24*self.multistaffing-5),
				h=int(self.h_note()*2),
				color=self.color_other,
			)
		#notes
		for i in self.staves_to_draw():
			for j in self.midi[1+i]:
				if not self.endures(j.ticks()): break
				if j.type()=='note':
					kwargs={
						'xi': self.x_ticks(j.ticks()),
						'xf': self.x_ticks(j.ticks()+j.duration()),
						'y' : self.y_note(i, j.number(), octaves[i]),
					}
					media.fill(
						h=int(self.h_note()),
						color=self.color_selected if self.is_selected(j) else self.color_notes,
						**kwargs
					)
					if j.number()-12*octaves[i]>24*self.multistaffing-4: media.fill(
						h=int(self.h_note()//2),
						color=self.color_warning,
						**kwargs
					)
				else: print(j)
		media.draw_vertices()
		#other events
		for i in self.midi[0]:
			text=None
			y=0
			if i.type()=='tempo':
				text='q={}'.format(int(us_per_minute/i.us_per_quarter()))
				y=10
			elif i.type()=='time_sig':
				text='{}/{}'.format(i.top(), i.bottom())
				y=20
			elif i.type()=='key_sig':
				def tonic(sharps, minor):
					return [
						'Cb', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F', 'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#'
					][7+sharps+(3 if minor else 0)]
				text='{}{}'.format(
					tonic(i.sharps(), i.minor()),
					'-' if i.minor() else '+'
				)
				y=30
			elif i.type()=='ticks_per_quarter': pass
			else: text=str(i)
			if text: media.text(text, x=self.x_ticks(i.ticks()), y=y, h=10, color=self.color_other)
		#cursor
		media.fill(
			xi=self.x_ticks(int(self.cursor.ticks)),
			xf=self.x_ticks(int(self.cursor.ticks+self.cursor.duration)),
			y=self.y_note(self.cursor.staff, self.cursor.note, octaves[self.cursor.staff]),
			h=int(self.h_note()),
			color=self.color_cursor,
		)
		#visual
		if self.visual.active:
			start, finish=self.get_visual_duration()
			media.fill(
				xi=self.x_ticks(int(start)),
				xf=self.x_ticks(int(finish)),
				y=self.y_note(self.visual.staff, self.notes_per_staff()-1),
				h=int(self.h_note()*self.notes_per_staff()),
				color=self.color_visual,
			)
		#text
		media.text(self.text, x=self.margin, y=self.h_window-self.margin, h=self.text_size, bottom=True)
		#
		media.display()
