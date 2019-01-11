#ifndef DLAL_BUFFER_INCLUDED
#define DLAL_BUFFER_INCLUDED

#include <skeleton.hpp>

#include <map>

namespace dlal{

class Buffer: public MultiOut, public Periodic, public SampleRateGetter{
	public:
		Buffer();
		std::string type() const { return "buffer"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
		float* audio();
		bool hasAudio(){ return true; }
		std::string resize(uint64_t period);
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
