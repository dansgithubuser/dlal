import dlal

import dansplotcore

from numpy.fft import fft

fr = [1, 0, 0, 0, 0.5, 0, 0, 0, 0.25, 0, 0, 0.5, 0, 0, 0]
ir = [float(abs(i)) for i in fft(fr)]

audio = dlal.Audio(driver=True)
iir = dlal.Iir()
buf = dlal.Buf()

iir.pole_pairs_bandpass(1000 / audio.sample_rate(), 0.01, pairs=4)

iir.connect(buf)

fr = dlal.frequency_response(buf, buf, n=4096)
dansplotcore.plot(fr)
