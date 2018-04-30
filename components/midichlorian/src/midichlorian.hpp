#ifndef DLAL_MIDICHLORIAN_INCLUDED
#define DLAL_MIDICHLORIAN_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Midichlorian: public MultiOut, public Periodic {
	public:
		Midichlorian();
		std::string type() const { return "midichlorian"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		std::string _rhythm="x";
		size_t _i=0;
};

}//namespace dlal

#endif
