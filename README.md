# dlal
dlal stands for Dan's Live Audio Lab.
The highest-level description of it is something that enables the user to explore and manipulate sound. Some example uses include
- design a sound from scratch
- run a digital jam session
- augment a real-life instrument

| Platform(s) | Status |
| --- | --- |
| OSX/Linux | [![Build Status](https://travis-ci.org/dansgithubuser/dlal.svg?branch=master)](https://travis-ci.org/dansgithubuser/dlal) |
| Windows | [![Build status](https://ci.appveyor.com/api/projects/status/tvni128gp6o02890/branch/master?svg=true)](https://ci.appveyor.com/project/dansgithubuser/dlal/branch/master) |

Try `python go.py -h` to get started.

## philosophy
dlal is cross-platform.
The benefit of being cross-platform is that as underlying systems change,
dlal remains capable of taking whatever best suits it.

dlal is conservative in its dependencies.
C++11, Python 3, and cmake are used to build.
As much as possible, dependencies are kept in-repo and reasonable errors should pop up if a requirement isn't met.
Despite this, build scripts should be flexible enough to use out-of-repo versions of dependencies.

## architecture
### C++ audio core
The core of the audio lab creates structure that allows for a tight audio thread capable of communicating with the outside world.
It should be easily embeddable into other environments.

A "tight" audio thread does none (or very little) of the following:
- memory allocation
- mutexing
- disk access
- waiting for UI, network, etc.
Communication with the above is enabled mainly with lockless queues.

#### skeleton
The skeleton defines the system and the abstract component.

##### system
The system minimally provides a way for components to communicate with each other before the audio thread starts, and defines an evaluation order for components.
In particular, as components are added to a system, they can set or get variables from the system.
In this way a set of components can agree on, say, a sample rate.
When the audio thread is going, it periodically requests audio data in a callback.
The system is evaluated once per callback.
In a system evaluation, each component is evaluated, in an order defined by the system.

The system is responsible for communicating with the environment it is embedded in, on a different thread than the audio thread.

#### components
Components provide a rich audio input, synthesis, manipulation, and output toolbox. Some key components follow.

##### audio
The audio component creates the audio thread and evaluates the system.
It is responsible for getting the result out into the real world as a sound.
The current implementation also listens to the microphone.

### Python
By wrapping the core in a Python environment, we get a nice language for audio system description.
We can also beef up what our components do outside the audio loop.

### interfaces
Interfaces enrich the ways in which someone can interact with the system. They communicate over the web, increasing the possible devices that can interact.

## file organization
### folders at multiple levels
- build folders are build descriptions for the item represented by the parent folder.
- deps folders are 3rd party dependencies for the item represented by parent folder.
- src folders are source code for the item represented by the parent folder.

### top level
- components: C++ components that can be connected to each other to create an audio system.
- dlal: Python module that wraps skeleton.
- midis: Collection of MIDIs, playable with midiplay system.
- skeleton: C++ library; audio system definition and abstract component definition.
- states: Collection of system states, loadable with loader system.
- systems: Python scripts that describe some useful audio systems.
- tests: Sanity tests.
- web: Web interfaces.

## todo
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
