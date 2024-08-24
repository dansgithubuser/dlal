import dlal

import dansplotcore

audio = dlal.Audio(driver=True)
iir = dlal.Iir()
buf = dlal.Buf()

iir.pole_pairs_bandpass( 800 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(1200 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(1600 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(2200 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(2400 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(2600 / audio.sample_rate(), 0.02, pairs=1, add=True)
iir.pole_pairs_bandpass(2000 / audio.sample_rate(), 0.02, pairs=1, add=True)

iir.connect(buf)

fr = dlal.frequency_response(buf, buf, n=4096)
dansplotcore.plot(fr)
