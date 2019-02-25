#ifndef DLAL_MIDICHLORIAN_INCLUDED
#define DLAL_MIDICHLORIAN_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Midichlorian: public MultiOut, public Periodic {
	public:
		Midichlorian();
		std::string type() const override { return "midichlorian"; }
		void evaluate() override;
	private:
		std::string _rhythm="x";
		size_t _i=0;
};

}//namespace dlal

#endif
