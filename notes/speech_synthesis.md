# goals
dlal's approach to speech synthesis has the following features:
- it learns phonetics from a recording
- it loosely mimics the vocal tract
- when synthesizing, it takes a tone source, a noise source, and a phonetic as input
- it can synthesize in real time

Regarding the first point: this feature prevents a kind of overfitting. If we truly understand how speech is synthesized, we should be able to extract parameters automatically.

# architecture
## recording
A practical set of English phonetics are recorded. They are recorded according to how they are produced.
- Voiced continuants are recorded following an unstressed vowel sound and slow transition.
- Unvoiced continuants are recorded in isolation.
- Stops are recorded unvoiced, each followed by an unvoiced unstressed vowel sound.
The recordee is encouraged to produce similar recordings, we must handle some amount of variance between recordings. For example one phonetic recording being louder than another.

## encoding
### sampling
Overlapping short-time Fourier transforms (STFTs) are taken. The tone and noise energy in the signal are estimated based on bin range and gain factor parameters and converted to amplitudes.

### modeling
For voiced continuants, formants are tracked from the unstressed vowel portion of the recording, and then measured. This helps ensure formants are not accidentally shuffled. The phonetic is then parameterized and framed.

For unvoiced continuants, the phonetic is immediately parameterized and framed.

For stops (which are recorded unvoiced), the first single utterance of the stop is taken. The start and end are found based on amplitude threshold parameters. The utterance is parameterized and framed.

#### parameterization
For voiced phonetics, formant frequencies and amplitudes are estimated. The amplitude of the formant is calculated based on the energy of the peak, with a parameter for how much of the peak to consider. The tone spectrum is estimated by taking bins above a threshold parameter.

The low end of the spectrum is discarded according to a threshold parameter. Based on this we estimate the center frequency of noise and the high noise component. The center frequency is an amplitude-based weighted average. The high noise is the energy in the signal above a frequency threshold parameter divided by the total energy of the signal.

The noise spectrum is estimated as the original signal's spectrum, with the first bin zeroed.

An overall amplitude is calculated from the tone and noise spectra.

The ratio between tone amplitude and total amplitude is calculated.

#### framing
Continuant parameters are averaged to produce a final result, rejecting outliers in the case of formant frequencies. The overall amplitude is set to 1.

Stop parameters are kept in a sequence. Their overall amplitudes are normalized so that every stop peaks at 1.

![record & encode](speech-record-encode.jpg)

## decoding
A sequence of phonetics (or syllables), timings (or notes), and pitches (or notes) are taken as input. Some phonetic rules are applied, such as ensuring silence before each stop, and how syllables should stretch or shrink in time.

Each phonetic is synthesized. Continuants have only one frame that is played continuously; stop frames are synthesized sequentially.

Formants are sent to a component that smoothly transitions between them, producing a spectrum each run, and fed to an additive sin bank synthesizer. The noise spectrum is fed to an additive noise bank synthesizer.

The noise signal is multiplied by the tone signal in such a way that voiced fricatives buzz and unvoiced fricatives are not silent.

The noise signal is multiplied by a tunable parameter.

![record & encode](speech-decode.jpg)

## vocoding
An input signal is parameterized and the result is directly synthesized. The tone spectrum is used instead of formants.

# math
The following section makes clear the (intended) connection between certain output characteristics in terms of all inputs and parameters.

## vocoder voiced fricative noise amplitude
```
synth_noise_amp = (noisebank_gain * noise_spectrum_amp) * (sinbank_gain * tone_spectrum_amp) * mutt_gain  # gains should each be 1
noise_spectrum_amp ~= recording_spectrum_amp
tone_spectrum_amp ~= recording_spectrum_amp
```

## decoder voiced fricative noise amplitude
```
synth_noise_amp = (noisebank_gain * noise_spectrum_amp) * (sinbank_gain * tone_spectrum_amp) * mutt_gain  # gains should each be 1
noise_spectrum_amp ~= recording_spectrum_amp
tone_spectrum_amp = formant_spectrum_amp  # which sounds about equal to `recording_spectrum_amp`
formant_spectrum_amp = forman_gain * model_formant_amp  # forman_gain should be 1
model_formant_amp = model_formant_gain * recording_formant_amp  # `model_formant_gain` is probably 1-ish, based on how wide the model guesses formants should be
```

# misc
## glottal source
Using a glottal source for the tone sounds more natural but doesn't seem more intelligible. Regardless, the system wouldn't live up to its goals if it depended on a glottal source to be intelligible.
