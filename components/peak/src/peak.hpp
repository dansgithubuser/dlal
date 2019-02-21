#ifndef DLAL_PEAK_INCLUDED
#define DLAL_PEAK_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Peak: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Peak();
		std::string type() const override { return "peak"; }
		void evaluate() override;
	private:
		struct Float{
			Float(): _(0.0f) {}
			float _;
		};
		std::map<Component*, Float> _peak;
		float _decay, _invertCoefficient, _invertOffset, _coefficient;
};

}//namespace dlal

#endif
