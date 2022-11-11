# imports
import dlal

# components
audio = dlal.Audio(driver=True)
liner = dlal.Liner()
porta = dlal.subsystem.Portamento()
synth = dlal.subsystem.SpeechSynth()
tape = dlal.Tape(1 << 16)

# connect
liner.skip_line(5)
dlal.connect(
    liner,
    porta,
    synth.tone,
    [],
    synth,
    tape,
)

# command
syllables = '''
    o.w [sh].i.t .i.ts g.e t.ns s.y r.y us

    .[ae].nd [th]r.w sm.ow.k h.y a p.y .[uu].d
    b.[ay]y.s m.[ae].n
    [th_v].u t.[ae]w.n h.[ae].d b.y.n .wi.[th_v] .aw.t b.[ay]y.s f.o[uu] o v.[uu] f.o[uu] t.y.0 y.i .[uu].z
    [th_v].eu w.u.z n.o.d [ae].n s.y.[ng]g
    [th_v].eu w.u.z n.o.0 rr.u.mp0 [sh].[ay]y k.y.[ng]g
    [th_v].eu h.[ae].d b.y.n n.o l.a.f t.u
    .[ae].nd 0d.e .e.[th]
    w.u.z n.y r.y.[ng]
    .e.v r.y b.a d.y
    .w.y k.[ae].n s.u[uu] v.a ay.v w.i [th_v].aw.t f.w .w.d
    b.u.t n.a.t w.i [th].aw.t b.[ay]y.s
    w.e.l n.a.t v.e r.y l.a.[ng]g .e n.y .wey
    [th_v].u.0 k.u l.u h.[ae].d jr.[ay]y.nd fr.u.m .e.v r.y w.u.nz f.[ay]y s.e.z
    .e.v r.y d.ey [th_v].u t.[ae]w.nz p.y p.l w.e.nt t.w [th_v].u [ch].[uu].[ch] .[ae].nd pr.[ay]y.d f.o[uu] b.[ay]y.s
    .[ae].nd b.[ay]y.s m.[ae].n l.[uu].kd .u p.a.n [th_v].u t.[ae]w.n .[ae].nd h.y sm.ay.ld f.o[uu] h.y ny.w
'''

model = dlal.speech.Model('assets/local/phonetic-model.json')

liner.load('assets/midis/audiobro3.mid', immediate=True)
u = dlal.speech.Utterance.from_syllables_and_notes(syllables, liner.get_notes(5), model)
u.print()
for phonetic, wait, pitch in u:
    synth.say(phonetic, model, wait)

# run
runs = int(240 * audio.sample_rate() / audio.run_size())
n = tape.size() // audio.run_size()
with open('assets/local/tmp.i16le', 'wb') as file:
    for i in range(runs):
        audio.run()
        if i % n == n - 1 or i == runs - 1: tape.to_file_i16le(file)
        print(f'{i / runs * 100:>6.2f}%', end='\r')
print()
dlal.sound.i16le_to_flac('assets/local/tmp.i16le', 'assets/local/audiobro3_voice.flac')
