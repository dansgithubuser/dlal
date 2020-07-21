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

dlal is an audio system configuration language Python module, that wrangles compiled audio processing components which abide a dead-simple C-linkage interface. This split is useful because Python is expressive, but compiled languages are fast, which we need in an audio processing environment.

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
| `DLAL_SNOOP_COMMAND` | snoop on commands |
| `DLAL_SNOOP_MIDI` | snoop on MIDI message |
| `DLAL_SNOOP_AUDIO` | snoop on this many percent of audio evaluations |
| `DLAL_SNOOP_AUDIO_SAMPLES` | snoop on this many samples of an audio evaluation, default 1 |

## layout
### files
- assets: static, purpose-built files
- components: audio processing components
	- base: abstract Rust base component
- skeleton: system configuration Python module, see below
- systems: multi-purpose audio system configurations
- web: GUI

## skeleton
### import graph
```
+===========+
| __init__  |
+===========+
^
|
+-+
| |
| +===========+
| | subsystem |
| +===========+
| ^
| |
+-+
|
+->------------>-+-> ( _server.serve )
|                |
+-+              +----------------------+
| |              |                      |
| +===========+  +===================+  +===================+
| | _skeleton |  | _websocket_server |  | _websocket_client |
| +===========+  +===================+  +===================+
| ^ ^            ^                      ^
| | |            |                      |
| +--------------+----------------------+
| | |
| | +--------------------------------------------+
| |                                              |
| +=========+                                    |
| | _server |                                    |
| +=========+                                    |
|                                                |
+------------------------+                       |
|                        |                       |
+=====================+  +=====================+ |
| _default_components |  | _special_components | |
+=====================+  +=====================+ |
^                        ^                       |
|                        |                       |
+------------------------+-----------------------+
|
+============+
| _component |
+============+

^
^
|
|# common resources
|
+------------+
|            |
+==========+ +========+
| _logging | | _utils |
+==========+ +========+
```

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

Additionally, components have an `evaluate` function called regularly when audio is being produced.

Components may register a `connect` command defining how to connect to another component. The other component is always connected as an _output_. That is, during evaluation, information should flow from this component to the other component. If a component registers `connect`, it should register a `disconnect` command as well.

Components may register `to_json` and `from_json` commands to accomplish serialization.

See `components/base` for more details and elaboration.

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
Driver components are responsible for calling `evaluate` on other components. In particular, they:
- have an `add` command that, on the Python side, takes a component as its first argument; and
- call `join` on all added components when they are added, conveying the `samples_per_evaluation` and `sample_rate` as kwargs.

The `audio` component is the driver component for interactive audio.

## todo
- clean up error handling and arg handling goes away
- get rid of json paranoia
- get rid of soul?
	- `commands!` section instead of individual `command!`s

- audiobro
	- track 1
		- bass slide down in B section
	- legend of bass
		- speech synth
			- LPC
			- https://www.youtube.com/watch?v=Jcymn3RGkF4
	- haunted by bass
	- bassindaface / funky funky bass
