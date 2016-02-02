#ifndef DLAL_LPF_INCLUDED
#define DLAL_LPF_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Lpf: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Lpf();
		std::string type() const { return "lpf"; }
		void evaluate();
	private:
		float _lowness;
		struct Float{
			Float(): _(0.0f) {}
			float _;
		};
		std::map<Component*, Float> _y;
};

}//namespace dlal

#endif
