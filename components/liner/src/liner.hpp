#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>

#include <atomiclist.hpp>
#include <midi.hpp>

#include <iostream>

namespace dlal{

class Liner: public MultiOut, public Periodic{
	public:
		struct Midi{
			uint64_t sample;
			std::vector<uint8_t> midi;
		};
		Liner();
		std::string type() const { return "liner"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
		std::string setPhase(uint64_t);
	private:
		void advance(uint64_t phase);
		void put(const uint8_t* midi, unsigned size, uint64_t sample);
		dlal::Midi getMidi(float samplesPerQuarter) const;
		std::string putMidi(dlal::Midi, float samplesPerQuarter);
		AtomicList<Midi> _line;
		AtomicList<Midi>::Iterator _iterator;
		bool _resetOnMidi;
};

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Liner::Midi& midi);

#endif
