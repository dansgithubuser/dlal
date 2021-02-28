dlal's approach to speech synthesis has the following features:
- it learns phonetics from a recording
- it models the vocal tract
- when synthesizing, it takes a tone source, a noise source, and a phonetic as input
- it can synthesize in real time

While the latter three features are common, the first is not. Not only is it cool to be able to create robotic voices based on human voices, it also prevents a kind of overfitting. If we truly understand how speech is synthesized, we should be able to extract parameters automatically.

## intelligibility
dlal's speech synthesis is not yet intelligible. Phonetics can be discerned if the listener can read the spoken sentence at the same time, but the sentence cannot be reliably heard from just the sound. Many ideas on how to improve are in the code and commit log. What is kept here are ideas that either never made it in, aren't fully explored, or just aren't clearly conveyed by their presence in the code and commit log.

### glottal source
Using a glottal source for the tone sounds more natural but doesn't seem more intelligible. Regardless, the system wouldn't live up to its goals if it depended on a glottal source to be intelligible.

### transitions
Switching between vocal tract paramters is done smoothly but simply. Formants are ordered from lowest to highest, and each formant smoothly moves from one individual set of parameters to the next. This helps make glides sound _more_ natural, but in reality only certain formants should morph into each other. For example, in "am", the overall volume is reduced, and resonances in the nose are emphasized. However, the system may morph a vocal tract formant into a nasal one.

So far this doesn't seem to be a big deal, aside from very chaotic changes. For example, if a formant morphs from low to high frequency, it can create an unintentional stop sound.

### filtering
A recording of actual speech has higher formants than the speech synth currently does. While the IIR bank approach offers the power of IIR filters and the flexibility of FIR filters, only single-pole IIR filters are being used.
