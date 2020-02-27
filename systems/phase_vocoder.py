import dlal

import atexit

system = dlal.System()
sample_rate = 44100
log_2_samples_per_evaluation = 6

with dlal.ImmediateMode() as mode:
    audio = dlal.Audio()
    audio.set(sample_rate, log_2_samples_per_evaluation)
    system.add(audio)

    buffer = dlal.Buffer()
    system.add(buffer)
    audio.connect(buffer)
    buffer.connect(audio)

    phase_vocoder = dlal.Component('phase_vocoder')
    system.add(phase_vocoder)
    phase_vocoder.connect(buffer)

audio.start()
atexit.register(lambda: audio.finish())
