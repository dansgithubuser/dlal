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
- audiobro
	- pitcher
		- slide: midi to audio [0, 127] -> [0, 1]
		- lfo
		- oracle: audio to control or command
	- reverb/chorus?
	- non-audio driver
	- tape to file

- burgers
	- arpeggiator
	- sample-based synth

- audiobro
	- legend of bass
		- speech synth
			- LPC
			- https://www.youtube.com/watch?v=Jcymn3RGkF4
	- haunted by bass
	- bassindaface / funky funky bass
