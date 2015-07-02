#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <RtMidi.h>

namespace dlal{

class Midi: public MultiOut{
	public:
		Midi();
		~Midi();
		void evaluate();
		void queue(const std::vector<uint8_t>&);
	private:
		std::string allocate();
		RtMidiIn* _rtMidiIn;
		Queue<std::vector<uint8_t>> _queue;
};

}//namespace dlal

#endif
