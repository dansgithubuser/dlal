import dlal

log2_samples_per_evaluation = 3
samples_per_evaluation = 1 << log2_samples_per_evaluation

# create
system = dlal.System()
raw = dlal.Component('raw')
liner = dlal.Liner(period_in_samples=8*samples_per_evaluation)
sonic_controller = dlal.SonicController()
# command
raw.set(44100, log2_samples_per_evaluation, immediate=True)
liner.loop_on_repeat(immediate=True)
liner.set_fudge(0, immediate=True)
sonic_controller.a(1, immediate=True)
sonic_controller.d(1, immediate=True)
sonic_controller.s(1, immediate=True)
sonic_controller.r(1, immediate=True)
# add
system.add(raw, slot=1, immediate=True)
system.add(liner, sonic_controller, immediate=True)
# connect
liner.connect(sonic_controller, immediate=True)
sonic_controller.connect(raw, immediate=True)
# start
raw.start(1, immediate=True)

def note(number, on):
    if on:
        cmd = 0x90
    else:
        cmd = 0x80
    liner.midi(cmd, number, 0x7f, immediate=True)
    sonic_controller.midi(cmd, number, 0x7f, immediate=True)

for i in range(2):
    note(60, True)
    raw.evaluate(immediate=True)
    note(60, False)
    for i in range(3):
        raw.evaluate(immediate=True)
    note(61, True)
    raw.evaluate(immediate=True)
    note(61, False)
    for i in range(3):
        raw.evaluate(immediate=True)

for i in range(8):
    raw.evaluate(immediate=True)
