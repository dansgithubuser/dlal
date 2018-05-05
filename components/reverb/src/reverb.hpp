#ifndef DLAL_REVERB_INCLUDED
#define DLAL_REVERB_INCLUDED

#include <skeleton.hpp>
#include <ringbuffer.hpp>

namespace dlal{

class Reverb: public MultiOut, public SamplesPerEvaluationGetter {
	public:
		Reverb();
		std::string type() const { return "reverb"; }
		void evaluate();
	private:
		float _amount;
		std::vector<ModRingbuffer<float>> _echos;
};

}//namespace dlal

#endif
