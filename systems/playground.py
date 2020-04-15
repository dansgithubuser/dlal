import dlal

import midi as mid

audio = dlal.Audio()
dlal.driver_set(audio)
comm = dlal.Comm()
midi = dlal.Midi()
gate_adsr = dlal.Adsr(1, 1, 1, 1e-5, name='gate_adsr')
gate_oracle = dlal.Oracle(format=('gain_y', '%'), name='gate_oracle')
adsr = dlal.Adsr(3e-6, 1, 1, 1e-4)
oracle = dlal.Oracle(
    'pitch_wheel',
    0x2000,
    0x2000,
    format=('midi', [0xe0, '%l', '%h']),
)
sonic = dlal.Sonic()
delay = dlal.Delay(22050, gain_x=0)
buf = dlal.Buf()

sonic.midi(mid.msg.pitch_bend_range(64))
sonic.from_json({
    "0": {
        "a": "1e-3", "d": "1e-3", "s": "1", "r": "1e-3", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.1",
    },
    "1": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "3": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
})

dlal.connect(
    [midi, '>', gate_adsr, '>', sonic],
    adsr,
    oracle,
    sonic,
    [buf, '<', delay, gate_oracle, gate_adsr],
    audio,
)

dlal.typical_setup()
