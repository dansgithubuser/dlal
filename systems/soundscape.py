import atexit
import dlal
import datetime
import glob
import os
import re


def timestamp():
    return '{:%Y-%m-%b-%d_%H-%M-%S}'.format(datetime.datetime.now()).lower()


system = dlal.System()
sample_rate = 44100
log_2_samples_per_evaluation = 8
seconds_per_evaluation = 1.0 * (1 << log_2_samples_per_evaluation)/sample_rate

audio = dlal.Component('audio')
audio.set(sample_rate, log_2_samples_per_evaluation)
system.add(audio)

recorder = dlal.Component('filea')
system.add(recorder)
recorder.open_write('soundscape_{}.flac'.format(timestamp()))
audio.connect(recorder)

commander = dlal.Commander()
system.add(commander)

ambient_sounds = {}
for i in glob.glob(os.path.join('..', '..', 'components', 'filea', 'ambient', '*.ogg')):
    filea = dlal.Component('filea')
    system.add(filea)
    filea.open_read(i)
    filea.set_volume(0)
    filea.loop_crossfade(4)
    filea.connect(audio)
    ambient_sounds[os.path.split(i)[-1][:-4]] = [filea, 0]


def get_ambient_sound(pattern):
    for k, v in ambient_sounds.items():
        if re.search(pattern, k):
            return v
    return None


def u(ambient_sound, volume=1, duration=5):
    x = get_ambient_sound(ambient_sound)
    commander.queue_command(x[0], 'fade', volume, duration)
    x[1] = volume


def d(ambient_sound, duration=5):
    x = get_ambient_sound(ambient_sound)
    commander.queue_command(x[0], 'fade', 0, duration)
    x[1] = 0


def l():
    for i in ambient_sounds.keys():
        print('{}: {}'.format(i, get_ambient_sound('^'+i+'$')[1]))


audio.start()
atexit.register(lambda: audio.finish())
print('audio processing going')
