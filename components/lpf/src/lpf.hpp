#ifndef DLAL_LPF_INCLUDED
#define DLAL_LPF_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Lpf:
	public MultiOut,
	public SamplesPerEvaluationGetter,
	public SampleRateGetter,
	public MidiControllee
{
	public:
		Lpf();
		std::string type() const { return "lpf"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
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
