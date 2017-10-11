#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>
#include <atomiclist.hpp>

#include <vector>
#include <cstdint>

namespace dlal{

class Liner: public MultiOut, public Periodic{
	public:
		Liner();
		std::string type() const { return "liner"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
		std::string setPhase(uint64_t);
	private:
		struct Midi{
			uint64_t sample;
			std::vector<uint8_t> midi;
		};
		void put(const uint8_t* midi, unsigned size, uint64_t sample);
		AtomicList<Midi> _line;
		AtomicList<Midi>::Iterator _iterator;
		bool _resetOnMidi;
};

}//namespace dlal

#endif
