#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <skeleton.hpp>

#include <RtMidi.h>

namespace dlal{

class Midi: public MultiOut{
	public:
		Midi();
		~Midi();
		std::string type() const { return "midi"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		std::string allocate();
		RtMidiIn* _rtMidiIn;
		Queue<std::vector<uint8_t>> _queue;
};

}//namespace dlal

#endif
