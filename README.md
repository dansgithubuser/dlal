dlal
====

high level description
----------------------
- run a digital jam session
- augment an instrument while playing it
- C++ for audio processing and Python for audio system description
- cross platform

features
--------
- FM synthesis modeled after the Sega Genesis YM2612 chip
- MIDI input
- SFML input
- mic input
- looping
- record and replay sessions

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

todo
----
- outputs should not know about inputs
- memory leak check
- midi split instrument
- fm pitch slide
- vocoder
- sampler
- low pass component
- diodefilter component
- pitch shift component
