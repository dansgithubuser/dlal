#ifndef DLAL_SOUNDFONT_INCLUDED
#define DLAL_SOUNDFONT_INCLUDED

#include <skeleton.hpp>

#include <fluidsynth.h>

#include <vector>

namespace dlal{

class Soundfont: public SamplesPerEvaluationGetter, public SampleRateGetter, public MultiOut {
	public:
		Soundfont();
		~Soundfont();
		std::string type() const override { return "soundfont"; }
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
	private:
		void destroy();
		std::string initialize();
		fluid_settings_t* _settings;
		fluid_synth_t* _synth;
		std::vector<float> _l, _r;
};

}//namespace dlal

#endif
