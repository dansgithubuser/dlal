#ifndef DLAL_MULTIPLIER_INCLUDED
#define DLAL_MULTIPLIER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Multiplier: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Multiplier();
		void evaluate();
	private:
		float _multiplier;
};

}//namespace dlal

#endif
