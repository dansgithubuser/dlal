#ifndef DLAL_ARPEGGIATOR_INCLUDED
#define DLAL_ARPEGGIATOR_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Arpeggiator: public MultiOut, public MidiControllee{
	public:
		Arpeggiator();
		std::string type() const { return "arpeggiator"; }
		void* derived(){ return this; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		std::map<uint8_t, uint8_t> _down;
		std::pair<uint8_t, uint8_t> _sounding;
		unsigned _i, _evaluation;
		float _evaluationsPerNote;
};

}//namespace dlal

#endif
