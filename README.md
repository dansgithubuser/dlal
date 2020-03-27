# dlal
dlal stands for Dan's Live Audio Lab.

dlal's goal is to enable experimentation with sound. Some example uses include
- design a sound from scratch
	- understand why a violin sounds different than 10 violins
	- compose music with arbitrary instruments or tunings
- augment a real-life instrument
- run a digital jam session
	- improvise with robots
	- play with a modular synth remotely
- record
	- in a failsafe manner
	- while controlling a soundscape
	- an entire jam session
- process existing recordings
	- apply an arbitrary effect chain to a recording
	- replay the inputs of a jam session

dlal is an audio system configuration module written in Python, that wrangles compiled audio processing components which abide the lv2 standard.

dlal is cross-platform.

Try `python do.py -h` to get started.

## todo
- dlal universal linkage
	- web interface
		- help/arg
		- two clients?
		- webboard
		- audio
		- sonic
	- clippy?
	- serialization
	- components
		- flesh out existing component features
		- buffer
		- arpeggiator
		- filei, fileo, filea
		- lpf
		- gain
		- reverb
		- liner
		- pitcher
	- audiobro

- burgers

- espeak? LPC

- music from formula with time as input

- operations in frequency domain
	- low pass amplitude of frequencies over time
		- for example, to extract the choral part of "Gangster's Paradise" which has many other fast-changing parts

- vocoder
- pitch shift component
- auto dj
- https://mutable-instruments.net/modules/
