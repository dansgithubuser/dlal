#===== imports =====#
import dlal

#===== system =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()
synth = dlal.subsystem.SpeechSynth()
tape = dlal.Tape(44100*5)

dlal.connect(
    synth,
    [audio, tape],
)

#===== main =====#
model = dlal.speech.Model('assets/local/phonetic-model.json')
run_size = audio.run_size()

def say(phonetic):
    info = model.phonetics[phonetic]
    for frame in info['frames']:
        synth.synthesize(
            frame['tone']['spectrum'],
            frame['noise']['spectrum'],
            frame['toniness'],
            run_size,
        )
    if info['type'] == 'stop':
        say('0')

dlal.typical_setup()
