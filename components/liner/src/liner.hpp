#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>

#include <vector>
#include <cstdint>

namespace dlal{

class Liner: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Liner();
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		struct Midi{
			Midi(uint64_t sample, const uint8_t* midi, unsigned size);
			uint64_t sample;
			std::vector<uint8_t> midi;
		};
		void put(const uint8_t* midi, unsigned size, uint64_t sample);
		std::vector<Midi> _line;
		unsigned _index;
		uint64_t _sample, _period;
};

}//namespace dlal

#endif
