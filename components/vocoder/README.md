A vocoder takes one input audio signal, the modulator, and modifies another audio signal, the carrier, based on the modulator.

The modulator is split into a number of bands, and the amplitude of each band is found. The same filtering is then applied to the carrier.

While this method is general, the bands themselves are made to be particularly useful when the modulator is human speech. In particular, by default, there are many equally-spaced narrow frequency bands in the 0 Hz to 4 kHz range, and one wide noise band for 8 kHz and above.
