import dlal

import atexit
import datetime

def timestamp():
    return '{:%Y-%m-%b-%d_%H-%M-%S}'.format(datetime.datetime.now()).lower()

system = dlal.System()
sample_rate = 44100
log_2_samples_per_evaluation = 8
recording_file_name = f'recording_{timestamp()}'

with dlal.ImmediateMode() as mode:
    audio = dlal.Audio()
    audio.set(sample_rate, log_2_samples_per_evaluation)
    system.add(audio)

    recorder = dlal.Component('filea')
    system.add(recorder)
    recorder.open_write(recording_file_name+'.flac')
    audio.connect(recorder)

audio.start()
atexit.register(lambda: audio.finish())
