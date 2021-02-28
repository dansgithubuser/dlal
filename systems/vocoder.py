import dlal

import time

audio = dlal.Audio(driver=True)
comm = dlal.Comm()
midi = dlal.Midi()
osc = dlal.Osc('saw')
audio.add(audio)
vocoder = dlal.Vocoder()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

dlal.connect(
    midi,
    osc,
    [buf, '<+', vocoder, audio],
    [audio, tape],
)

dlal.typical_setup()

def on():
    midi.midi([0x90, 41, 0x40])

def off():
    midi.midi([0x80, 41, 0x40])

def rec(duration=5, pause=3):
    print('recording in')
    for i in range(pause, 0, -1):
        print(i)
        time.sleep(1)
    print('recording')
    tape.to_file_i16le_start()
    for i in range(duration):
        print(f'{i} / {duration}')
        time.sleep(1)
    tape.to_file_i16le_stop()
    print('done')
