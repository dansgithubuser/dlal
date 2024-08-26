import dlal

import dansplotcore

audio = dlal.Audio(driver=True)
iir = dlal.Iir()
buf = dlal.Buf()

iir.pole_pairs_bandpass(1000 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(1500 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(2500 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(3000 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(3500 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(4000 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(5000 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(6000 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(7000 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(8000 / audio.sample_rate(), 0.03, pairs=1, add=True)
iir.pole_pairs_bandpass(2000 / audio.sample_rate(), 0.03, pairs=1, add=True)

iir.connect(buf)

fr = dlal.frequency_response(buf, buf, n=4096)
dansplotcore.plot(fr)
