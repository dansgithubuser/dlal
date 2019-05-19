#ifndef DLAL_PITCHER_INCLUDED
#define DLAL_PITCHER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Pitcher: public SampleRateGetter, public SamplesPerEvaluationGetter, public MultiOut{
	public:
		Pitcher();
		std::string type() const override { return "pitcher"; }
		void* derived() override { return this; }
		std::string connect(Component& output) override;
		std::string disconnect(Component& output) override;
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
	private:
		using Midi=std::vector<uint8_t>;
		void noteOn(const uint8_t* bytes);
		void noteOff(const uint8_t* bytes);
		float
			_glissSeparation=0.1f,
			_glissRate=1.0f,
			_vibratoRate=4.0f,
			_vibratoAmount=0.0f,
			_silence,
			_phase=0.0f,
			_pitch=float(0x2000),
			_pitchDst=float(0x2000);
		uint8_t _on=0x80;
		std::vector<uint8_t> _off;
};

}//namespace dlal

#endif
