#ifndef DLAL_PHASE_VOCODER_INCLUDED
#define DLAL_PHASE_VOCODER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class PhaseVocoder: public MultiOut, public SampleRateGetter, public SamplesPerEvaluationGetter {
	public:
		PhaseVocoder();
		~PhaseVocoder();
		std::string type() const override { return "phase_vocoder"; }
		void* derived() override { return this; }
		void evaluate() override;
	private:
		void* plugin=nullptr;
};

}//namespace dlal

#endif
