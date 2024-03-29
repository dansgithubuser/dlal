# goals
dlal's approach to speech synthesis has the following features:
- it learns phonetics from a recording (magic numbers don't correspond to an individual voice)
- it loosely mimics the vocal tract (we can experiment with voice-like sound processing)
- it can synthesize in real time (it can be used in a live performance)

# architecture
## recording
A practical set of English phonetics are recorded. They are recorded according to how they are produced.
- Voiced continuants are recorded following an unstressed vowel sound and slow transition.
- Unvoiced continuants are recorded in isolation.
- Stops are recorded unvoiced, each followed by an unvoiced unstressed vowel sound.
- Voiced stops are rerecorded around an unstressed vowel.
Although the recordee is encouraged to produce similar recordings, we must handle some amount of variance between recordings. For example one phonetic recording being louder than another.

## encoding
### sampling
Overlapping short-time Fourier transforms (STFTs) are taken. For each, the tone and noise energy in the signal are estimated based on bin range and gain factor parameters and converted to amplitudes. So samples have the form `[(spectrum, amp_tone, amp_noise), ...]`.

### modeling
Samples are selected, converted to speech parameters, and framed to express how the phonetic changes over time. Continuant, stop, voiced, and unvoiced phonetics may be treated differently at each step.

#### selection
For voiced continuants, formants are tracked from the unstressed vowel portion of the recording, and then selected. This ensures formants are not accidentally shuffled.

For unvoiced continuants, all samples are selected.

For stops (which are recorded unvoiced), the first single utterance of the stop is selected. The start and end are found based on amplitude threshold parameters.

Voiced stops have an additional recording surrounding an unstressed vowel. Formants are tracked from the vowel portion of the recording backward to the start of the stop. The start is found based on noise amplitude threshold parameters.

#### parameterization
For voiced continuants, formant frequencies and amplitudes are estimated. The amplitude of the formant is calculated based on the energy of the peak, with a parameter for how much of the peak to consider. The tone spectrum is estimated by taking bins below a frequency threshold parameter and above an amplitude threshold parameter.

The low end of the spectrum is discarded according to a threshold parameter. Based on this we estimate the center frequency of noise and the high noise component. The center frequency is an amplitude-based weighted average. The high noise is the energy in the signal above a frequency threshold parameter divided by the total energy of the signal.

The noise spectrum is estimated as the original signal's spectrum, with the first bin zeroed.

An overall amplitude is calculated from the tone and noise spectra.

The ratio between tone amplitude and total amplitude is calculated.

#### framing
Continuant parameters are averaged to produce a final result, rejecting outliers in the case of formant frequencies. The overall amplitude is set to 1.

Stop parameters are kept in a sequence. Their overall amplitudes are normalized so that every stop peaks at 1.

## record & encode diagram
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
