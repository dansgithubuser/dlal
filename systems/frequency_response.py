import dlal

import dansplotcore

from numpy.fft import fft

fr = [1, 0, 0, 0, 0.5, 0, 0, 0, 0.25, 0, 0, 0.5, 0, 0, 0]
ir = [float(abs(i)) for i in fft(fr)]

audio = dlal.Audio(True)
fir = dlal.Fir(ir)
buf = dlal.Buf()

fir.connect(buf)

fr = dlal.frequency_response(buf, buf, n=4096)
dansplotcore.plot(fr)
