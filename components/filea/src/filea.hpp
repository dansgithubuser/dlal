#ifndef DLAL_FILEA_INCLUDED
#define DLAL_FILEA_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Filea: public MultiOut, public SamplesPerEvaluationGetter, public SampleRateGetter{
	public:
		Filea();
		~Filea();
		std::string type() const { return "filea"; }
		void evaluate();
		float* audio();
		bool hasAudio(){ return true; }
	private:
		std::vector<float> _audio;
		void* _i;
		void* _o;
};

}//namespace dlal

#endif
