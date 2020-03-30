import dlal

import atexit
import sys

dlal.system_load(sys.argv[1], globals())

if 'audio' in globals():
    audio.start()
    atexit.register(lambda: audio.stop())
if 'comm' in globals():
    dlal.queue_set(comm)
dlal.serve()
