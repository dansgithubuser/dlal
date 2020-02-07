import dlal

import atexit
import datetime
import time

def timestamp():
    return '{:%Y-%m-%b-%d_%H-%M-%S}'.format(datetime.datetime.now()).lower()

system = dlal.System()
sample_rate = 44100
log_2_samples_per_evaluation = 8
recording_name = f'recording_{timestamp()}'

with dlal.ImmediateMode() as mode:
    audio = dlal.Audio()
    audio.set(sample_rate, log_2_samples_per_evaluation)
    system.add(audio)

    recorder_a = dlal.Component('filea')
    system.add(recorder_a)
    recorder_a.open_write(recording_name+'.flac')
    audio.connect(recorder_a)

    recorder_o = dlal.Component('fileo')
    recorder_o.file_name(recording_name+'.txt')
    system.add(recorder_o)
    audio.connect(recorder_o)

audio.start()
atexit.register(lambda: audio.finish())
system.serve()

time.sleep(1)

monitor = dlal.Component('filei')
monitor.stream(recording_name+'.txt')
system.add(monitor)
monitor.connect(audio)
