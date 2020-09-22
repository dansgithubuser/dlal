import dlal

import random

# setup
audio = dlal.Audio()
dlal.driver_set(audio)
iir = dlal.Iir()
buf = dlal.Buf()
tape = dlal.Tape()

iir.connect(buf)
buf.connect(tape)

# helpers
def test(b, a, x, y, name):
    print(name, end=' ')
    # setup
    with dlal.Immediate():
        buf.set(x)
        iir.b(b)
        iir.a(a)
    audio.run()
    # check
    y_actual = tape.read()
    error = 0
    for i in range(len(y)):
        error += abs(y_actual[i] - y[i])
    if error > 1e-6:
        print('error')
        print(f'expected: {y}')
        print(f'actual  : {y_actual[0:len(y)]}')
    else:
        print('ok')
    # clear
    with dlal.Immediate():
        iir.b([0])
        iir.a([1])
    audio.run()
    tape.read()

# signals
one = [1] * 4
zero = [0] * 4

# filters
a_lpc_ae = [
    1,
    -1.2339960312158325, 1.4100019757067805, -1.516738394853675, 1.375770418344785, -1.1674011127114041,
    0.9433608853175482, -0.6759263973471616, 0.43625452612997545, -0.269208064958481, 0.12509040286574277,
    -0.02382315739116951, -0.03155797246948581, 0.10266808262300961, -0.13727452397223533, 0.12129995384479633,
    -0.11046111607642219, 0.08717625320776409, -0.047650678211978145, 0.01764409294592785, 0.00047204848770017113,
    -0.010272381370959746, 0.009015823004686101, -0.0026029000784035137, 0.029529760587273596,
]

# tests
test([0], [1], one, zero, 'all-stop')
test([1], [1], one, one, 'all-pass')
test([0.5], [1, -0.5], one, [1/2, 3/4, 7/8, 15/16], 'low-pass')
test([1], a_lpc_ae, one, [1, 2.23399603, 2.34674026, 2.26266774], 'a_lpc_ae')
