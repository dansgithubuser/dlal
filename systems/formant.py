import dlal

import tkinter

with dlal.ImmediateMode() as mode:
    # components
    s_voice = dlal.Sonic(); s_voice.i(0, 0, 0.25); s_voice.s(0, 1); s_voice.midi(0x90, 40, 0x7f)
    s_noise = dlal.Sonic()
    s_noise.i(0, 0, 4.00); s_noise.i(0, 1, 4.00)
    s_noise.i(1, 0, 4.00); s_noise.i(1, 1, 4.00)
    s_noise.m(1, 0.01)
    s_noise.midi(0x90, 41, 0x7f)
    f_voice = dlal.Formant(); f_voice.resize(128)
    f_noise = dlal.Formant(); f_noise.resize(128)
    multiplier = dlal.Component('multiplier'); multiplier.offset(1); multiplier.set(0.5); multiplier.gate(-0.001)
    buffer_voice = dlal.Buffer(); buffer_voice.clear_on_evaluate('y')
    buffer_noise = dlal.Buffer(); buffer_noise.clear_on_evaluate('y')
    # system
    s_voice.connect(buffer_voice); f_voice.connect(buffer_voice)
    s_noise.connect(buffer_noise); f_noise.connect(buffer_noise)
    multiplier.connect(buffer_voice); multiplier.connect(buffer_noise)
    system = dlal.SimpleSystem(
        [s_voice, s_noise, f_voice, f_noise, multiplier, buffer_voice, buffer_noise],
        [s_voice, s_noise],
        [buffer_voice, buffer_noise]
    )
# phonetic interface
root = tkinter.Tk()
root.title('formant')
def key_press(event):
    if event.keysym == 'Escape':
        root.destroy()
        return
    f_voice.phonetic_voice(event.char)
    f_noise.phonetic_noise(event.char)
root.bind_all('<KeyPress>', key_press)
# go
go, ports = system.standard_system_functionality()
