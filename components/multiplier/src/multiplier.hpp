#ifndef DLAL_MULTIPLIER_INCLUDED
#define DLAL_MULTIPLIER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Multiplier: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Multiplier();
		std::string type() const { return "multiplier"; }
		void evaluate();
	private:
		float _multiplier, _offset, _gate;
};

}//namespace dlal

#endif
