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

dlal is an audio system configuration module written in Python, that wrangles compiled audio processing components which abide a dead-simple C-linkage interface.

dlal's GUI is web-based.

dlal is cross-platform.

Try `python do.py -h` to get started.

## todo
- dlal universal linkage
	- web interface
		- webboard
		- audio
		- sonic
	- serialization
	- mic
	- components
		- buffer
		- filei, fileo, filea
		- lpf
		- gain
		- reverb
		- liner
		- pitcher
	- audiobro
		- midi editor
		- chorus?

- burgers
	- arpeggiator
	- sample-based synth

- speech synth
	- LPC
	- https://www.youtube.com/watch?v=Jcymn3RGkF4

- pitch shift component
