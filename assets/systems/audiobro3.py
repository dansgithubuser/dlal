import dlal

import midi

import sys

def sys_arg(i):
    if len(sys.argv) > i:
        return sys.argv[i]

#===== init =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

# bassoons
bassoon1 = dlal.Buf('bassoon', name='bassoon1')
bassoon2 = dlal.Buf('bassoon', name='bassoon2')
# accordion
accordion1 = dlal.Buf('melodica', name='accordion1')
accordion2 = dlal.Buf('melodica', name='accordion2')
# drum
drum = dlal.Buf(name='drum')
# voice
voice_porta = dlal.subsystem.Portamento(name='voice_porta')
voice_tone = dlal.Train(name='voice_tone')
voice_noise = dlal.Osc('noise', name='voice_noise')
voice_phonetizer = dlal.subsystem.Phonetizer(tone_pregain=5, noise_pregain=1.5)
# guitar
guitar_strummer = dlal.Strummer(name='guitar_strummer')
guitar = dlal.Buf('guitar', name='guitar')
# shaker
shaker1 = dlal.Buf(name='shaker1')
shaker2 = dlal.Buf(name='shaker2')

liner = dlal.Liner()
reverb = dlal.Reverb(0.1)
lim = dlal.Lim(1, 0.9, 0.3)
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

#===== commands =====#
#----- bassoons -----#
bassoon1.repeat()
bassoon2.repeat()
bassoon1.normalize(0.3)
bassoon2.normalize(0.3)

#----- accordion -----#
accordion1.repeat()
accordion2.repeat()
accordion1.normalize(0.1)
accordion2.normalize(0.1)

#----- drum -----#
# bass
drum.load('assets/sounds/drum/bass.wav', 35)
drum.crop(0, 0.2, 35)
drum.load('assets/sounds/drum/bass.wav', 36)
drum.crop(0, 0.2, 36)
# snare
drum.load('assets/sounds/drum/snare.wav', 38)
drum.clip(0.5, 38)
# hat
drum.load('assets/sounds/drum/hat.wav', 42)
# crash
drum.load('assets/sounds/drum/crash.wav', 57)
# side stick
drum.load('assets/sounds/drum/side-stick.wav', 37)
drum.resample(1.5, 37)
drum.amplify(2, 37)
drum.crop(0, 0.07, 37)
# ride bell
drum.load('assets/sounds/drum/ride-bell.wav', 55)

#----- guitar -----#
guitar_strummer.pattern(
    'd u udu u ududu'
    'd u udu u ududu'
    'd u udu u ududu'
    'd u udu u udd'
)
guitar.normalize(0.3)

#----- shakers -----#
shaker1.load('assets/sounds/drum/shaker1.wav', 82)

shaker2.load('assets/sounds/drum/shaker2.wav', 82)
shaker2.amplify(0.5, 82)

#----- liner -----#
liner.load('assets/midis/audiobro3.mid', immediate=True)
liner.advance(float(sys_arg(1) or 0))

#----- voice -----#
voice_phonetizer.prep_syllables(
    '''
        o.w [sh].i.t .i.ts g.e t.ns s.y r.y .u.s

        .[ae].nd [th]r.w sm.ow.k h.y a p.y .[uu].d
        b.[ay]y.s m.[ae].n
        [th_v].u t.[ae]w.n h.[ae].d b.y.n .wi.[th_v] .aw.t b.[ay]y.s f.o[uu] o v.[uu] f.o[uu] t.y.0 y.i .[uu].z
        [th_v].eu w.u.z n.o.0 d.[ae].n s.y.[ng]g
        [th_v].eu w.u.z n.o.0 rr.u.mp0 [sh].[ay]y k.y.[ng]g
        [th_v].eu h.[ae].d b.y.n n.o l.a.f t.u
        .[ae].nd 0d.e .e.[th]
        w.u.z n.y r.y.[ng]
        .e.v r.y b.a d.y
        .w.y k.[ae].n s.u[uu] v.a ay.v w.i [th_v].aw.t f.w .w.d
        b.u.t n.a.t w.i [th].aw.t b.[ay]y.s
        w.e.l n.a.t v.e r.y l.a.[ng]g .e n.y .wey
        [th_v].u.0 k.u l.u[uu] h.[ae].d jr.[ay]y.nd fr.u.m .e.v r.y w.u.nz f.[ay]y s.e.z
        .e.v r.y d.ey [th_v].u t.[ae]w.nz p.y p.l w.e.nt t.w [th_v].u [ch].[uu].[ch] .[ae].nd pr.[ay]y.d f.o[uu] b.[ay]y.s
        .[ae].nd b.[ay]y.s m.[ae].n l.[uu].kd .u p.a.n [th_v].u t.[ae]w.n .[ae].nd h.y sm.ay.ld f.o[uu] h.y ny.w
    ''',
    liner.get_notes(5),
    advance=int(float(sys_arg(1) or 0) * audio.sample_rate()),
    anticipation=0
)

#===== connect =====#
dlal.connect(
    liner,
    [
        bassoon1,
        bassoon2,
        accordion1,
        accordion2,
        drum,
        [voice_porta, '>',
            (voice_tone, voice_noise),
            (voice_phonetizer.tone_buf, voice_phonetizer.noise_buf),
        ],
        [guitar_strummer, '>', guitar],
        shaker1,
        shaker2,
    ],
    [buf,
        '<+', voice_phonetizer,
        '<+', guitar,
        '<+', reverb,
        '<+', lim,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup()
