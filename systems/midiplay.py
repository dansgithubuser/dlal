import argparse
import atexit
import dlal
import os

try:
    input = raw_input
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('file_path')
args = parser.parse_args()
if not os.path.exists(args.file_path):
    args.file_path = os.path.join('..', '..', args.file_path)

# construct
system = dlal.System()
liners = [dlal.Liner()]
soundfont = dlal.Soundfont()
audio = dlal.Audio()

# connect
dlal.connect(liners[0], soundfont, audio, immediate=True)

# add
system.add(liners[0], slot=0, immediate=True)
system.add(soundfont, audio, slot=1, immediate=True)

# command
soundfont.load(os.path.join('..', '..', 'components', 'soundfont', 'deps', '32MbGMStereo.sf2'), immediate=True)
atexit.register(lambda: audio.finish())

# interface
playing = False

def play_start():
    global liners
    # infrastructure for more tracks
    regular_tracks = len(dlal.midi.read(args.file_path)) - 1
    more = regular_tracks - len(liners)
    if more > 0:
        new_liners = [dlal.Liner() for _ in range(more)]
        for i in new_liners:
            i.connect(soundfont, immediate=True)
            system.add(i, slot=1, immediate=True)
        liners += new_liners
    elif more < 0:
        for i in liners[regular_tracks:]:
            i.clear(immediate=True)
    # load
    for i in range(len(liners)):
        liners[i].load(args.file_path, 22050, i+1, immediate=True)
    periods = []
    for i in liners:
        i.periodic_set_phase(0, immediate=True)
        periods.append(i.period(immediate=True))
    for i in liners:
        i.periodic_resize(max(periods), immediate=True)
    # play
    audio.start()
    global playing
    playing = True

def play_stop():
    audio.finish()
    soundfont.reset(immediate=True)
    global playing
    playing = False

def play_toggle():
    if not playing:
        play_start()
        return 'playing'
    else:
        play_stop()
        return 'stopped'

class ReprFunction:
    def __init__(self, function): self.function = function
    def __repr__(self): return self.function()

p = ReprFunction(play_toggle)
print(repr(p))
