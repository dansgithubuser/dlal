import os

import dlal

buffer = dlal.Buffer()
system = dlal.SimpleSystem([buffer])
buffer.load_sound(0, os.environ['DLAL_SOUND_FILE'])
buffer.pitch_sound('y', immediate=True)
buffer.elongate_sound('y', immediate=True)
go, ports = system.standard_system_functionality()
qweboard = dlal.Qweboard(buffer)
