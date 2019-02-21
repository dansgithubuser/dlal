#ifndef DLAL_BUFFER_INCLUDED
#define DLAL_BUFFER_INCLUDED

#include <skeleton.hpp>

#include <map>

namespace dlal{

class Buffer: public MultiOut, public Periodic, public SampleRateGetter{
	public:
		Buffer();
		std::string type() const override { return "buffer"; }
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
		float* audio() override;
		bool hasAudio() override { return true; }
		std::string resize(uint64_t period) override;
	private:
		struct Playing{
			Playing(){}
			Playing(float volume): volume(volume), sample(0.0f) {}
			float sample, volume;
		};
		std::string checkSize(uint64_t period);
		std::vector<float> _audio;
		bool _clearOnEvaluate, _repeatSound, _pitchSound;
		std::vector<std::vector<float>> _sounds;
		std::map<unsigned, Playing> _playing;
};

}//namespace dlal

#endif
