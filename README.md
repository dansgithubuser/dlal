# dlal
## intro
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

dlal is an audio system configurator Python module, that wrangles compiled audio processing components which abide a dead-simple C-linkage interface. This split is useful because Python is expressive, but compiled languages are fast. We want expressiveness for the human describing how sound should be procued, and speed for actually making the sound.

dlal's GUI is web-based.

dlal is cross-platform.

## getting started
```
git clone --recurse-submodules https://github.com/dansgithubuser/dlal #to clone
cd dlal
./do.py --vf; . venv-on #to create a venv (optional)
./do.py --vi #to install Python dependencies
./do.py -b #to build
./do.py -r systems/sonic.py #to run a simple synthesizer system
./do.py -w #in another terminal session to start web GUI
```

In the browser tab that opens, you can click on the `sonic` component, then on `webboard`.
In the webboard, you can click `connect` and play the keyboard.

You can explore the interactive Python UI of dlal in the original terminal session as well.

## environment variables
| var | description |
| - | - |
| `DLAL_MIDI_INPUT` | which MIDI port to open by default when initializing a `dlal.Midi` |
| `DLAL_TO_FILE` | when using `dlal.typical_setup`, record to file for this many seconds instead of playing live |
| `DLAL_LOG_LEVEL` | critical, error, warning (default), info, debug, verbose |
| `DLAL_SNOOP_CONNECT` | snoop on connections |
| `DLAL_SNOOP_COMMAND` | snoop on commands |
| `DLAL_SNOOP_MIDI` | snoop on MIDI message |
| `DLAL_SNOOP_AUDIO` | snoop on this many percent of audio runs |
| `DLAL_SNOOP_AUDIO_SAMPLES` | snoop on this many samples of an audio run, default 1 |

## layout
### files
- assets: static, purpose-built files
- components: audio processing components
	- base: abstract Rust base component
- skeleton: system configuration Python module, see below
- systems: multi-purpose audio system configurations
- web: GUI

## skeleton
### server
Not to be confused with the simple HTTP file server run via `./do.py -w`, the skeleton server allows arbitrary dlal operation over the web.

The typical implementation is in `skeleton/dlal/_websocket_server.py`.

The abstract server, and therefore clients, communicate with JSON with the following structure:

request (client to server):
```
{
	uuid,     # unique identifier for this request
	path,     # path from the root of the server to the value being operated on
	args,     # optional, default `[]`
	kwargs,   # optional, default `{}`
	op,       # optional, 'store' or 'free'
}
```
response (server to client):
```
{
	result,
	error,    # if there's an error
	...request,
}
```
broadcast (server to client):
```
{
	topic,
	message,
	op,       # must be 'broadcast'
}
```

The abstract server can be found in `skeleton/dlal/_server.py`

## components
Components interact in 3 ways:
- commands (text)
- MIDI
- audio (constant-size arrays)

Audio is unique because it is exposed as a value, whereas the command and MIDI interfaces are functions. For this reason, audio is useful for conveying quantities other than actual audio. For example, components may share control voltage via the audio interface. Arguably, audio is one example of control voltage, but it is named for how it is usually, or at least necessarily, used.

Additionally, components have an `run` function called regularly when audio is being produced.

Components may register a `connect` command defining how to connect to another component. The other component is always connected as an _output_. That is, during run, information should flow from this component to the other component. If a component registers `connect`, it should register a `disconnect` command as well.

Components may register `to_json` and `from_json` commands to accomplish serialization.

See `components/base` for more details.

On the Python side, components may implement `get_cross_state` and `set_cross_state` methods to accomplish serialization of cross-component information.

Components may have local README.md files explaining their specific functionality.

### command structure
Commands are JSON with the following structure:
```
{
	name,
	args,
	kwargs,
}
```

Responses can be any JSON, but they should be an object with an `error` value to indicate error.

See `skeleton/dlal/_component.py` for more details.

### driver components
Driver components are responsible for calling `run` on other components. In particular, they:
- have an `add` command that, on the Python side, takes a component as its first argument; and
- call `join` on all added components when they are added, conveying the `run_size` and `sample_rate` as kwargs.

The `audio` component is the driver component for interactive audio.

## todo
use voiced stops at end of context

compare freq spectrum

formants for all phonetics?

[00:00.000 --> 00:03.300]  Oh shit, it's getting serious.
[00:00.000 --> 00:01.440]  and through the field
[00:01.440 --> 00:04.380]  placeman
[00:04.380 --> 00:15.000]  The town had been without a school for 40 years
[00:15.000 --> 00:20.100]  There was no dancing
[00:20.100 --> 00:23.440]  There was no rock shaking
[00:23.440 --> 00:27.880]  There had been no laughter
[00:30.260 --> 00:32.040]  And death
[00:32.040 --> 00:35.640]  Was nearing everybody
[00:35.640 --> 00:40.180]  We can survive without food
[00:40.180 --> 00:43.620]  But not without place
[00:43.620 --> 00:45.600]  Well
[00:45.600 --> 00:49.460]  Not very long anyway
[00:49.460 --> 00:55.760]  The color had rained from everyone's faces
[01:01.700 --> 01:06.580]  Every day the town people went to the pool and played with place
[01:06.580 --> 01:16.160]  And placeman looked upon the town and he smiled for he knew

- audiobro
	- review existing tracks
	- bassindaface / funky funky bass

- be able to open audio callback in more situations for demonstrating on skype
- change verbiage to connector/connectee instead of input/output
