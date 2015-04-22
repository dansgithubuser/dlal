#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <RtMidi.h>

namespace dlal{

class Midi: public Component{
	public:
		Midi();
		~Midi();
		void evaluate(unsigned samples);
		MidiMessages* readMidi();
		void queue(const MidiMessage&);
	private:
		std::string allocate();
		RtMidiIn* _rtMidiIn;
		Queue<MidiMessage> _queue;
		MidiMessages _messages;
};

}//namespace dlal

#endif
