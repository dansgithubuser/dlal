dlal
====
dlal stands for Dan's Live Audio Lab.
The highest-level description of it is something that enables the user to explore and manipulate sound.

design
------
dlal uses C++ for audio processing and Python for audio system description.
C++ is well-suited to the timing constraints of audio processing.
Python is easily written and customized to create your ideal audio system.

dlal is cross-platform.
The benefit of being cross-platform is that as underlying systems change,
dlal remains capable of taking whatever best suits it.
So far this is loosely enforced.
I've had luck on Windows 10 and OSX 10.9, and trouble on Trusty Tahr.

dlal is conservative in its dependencies.
C++11, Python (2 or 3), and cmake are used to build.
Audio is built on PortAudio.
As much as possible, dependencies are kept in-repo and reasonable errors should pop up if a requirement isn't met.
Despite this, build scripts should be flexible enough to use out-of-repo versions of dependencies.

example uses
------------
- design a sound from scratch
- run a digital jam session
- augment a real-life instrument

features
--------
- FM synthesis modeled after the Sega Genesis YM2612 chip
- MIDI input
- mic input
- SFML input and output over a network
- looping
- record and replay sessions
- networking
- SoundFont
- VST host

file organization
-----------------
- skeleton: C++ library; audio system definition and abstract component definition.
- components: C++ components that can be connected to each other to create an audio system. Each has:
	- build: Build description.
	- deps: 3rd party dependencies.
	- src: Source code.
- build: Overall build description.
- dlal: Python module that wraps skeleton.
- systems: Python scripts that describe some useful audio systems.
- interfaces: Interfaces that communicate with audio systems over the network.
- tests: Sanity tests.

todo
----
- vst host, use 8bitZ as motivation
	- two vsts at the same time
	- mac, linux
- just use std::cerr instead of error reporting
- soundboard
	- doioioioing
	- toilet
	- meow, bark, cuckoo, bok bok bok, mooo
- robot voice
- looping
- sampling
- dance suit (expand)
- simple improvements
	- fm pitch slide
	- lfo
	- arpeggiator
- possible future features
	- looper: quantization
	- vocoder
	- pitch shift component
	- auto dj
