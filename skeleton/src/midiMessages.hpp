#ifndef DLAL_MIDI_MESSAGES_INCLUDED
#define DLAL_MIDI_MESSAGES_INCLUDED

#include <cstdint>
#include <vector>

namespace dlal{

struct MidiMessage{
	static const unsigned SIZE=4;
	MidiMessage();
	MidiMessage(const std::vector<uint8_t>&);
	uint8_t _bytes[SIZE];
};

class MidiMessages{
	public:
		MidiMessages();
		MidiMessages(const MidiMessage&);
		MidiMessage& operator[](unsigned);
		const MidiMessage& operator[](unsigned) const;
		unsigned size() const;
		bool push_back(const MidiMessage&);
		bool push_back(const MidiMessages&);
		void clear();
	private:
		static const unsigned SIZE=256;
		MidiMessage _messages[SIZE];
		unsigned _size;
};

}//namespace dlal

#endif//#ifndef DLAL_MIDI_MESSAGES_INCLUDED
