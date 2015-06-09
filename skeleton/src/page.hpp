#ifndef DLAL_PAGE_INCLUDED
#define DLAL_PAGE_INCLUDED

#include "midiMessages.hpp"

#include <string>
#include <vector>
#include <fstream>
#include <cstdint>

namespace dlal{

struct Page{
		bool fromAudio(float* audio, unsigned size, uint64_t evaluation);
		bool fromMidi(MidiMessages* midi, uint64_t evaluation);
		bool fromText(std::string* text, uint64_t evaluation);
		void toFile(std::ostream&);
		void fromFile(std::istream&);
		enum Type{ AUDIO, MIDI, TEXT };
		Type _type;
		uint64_t _evaluation;
		std::vector<float> _audio;
		MidiMessages _midi;
		std::string _text;
};

}//namespace dlal

#endif
