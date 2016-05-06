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
		void resize(uint64_t period);
	private:
		std::vector<float> _audio;
		bool _clearOnEvaluate, _repeatSound, _pitchSound;
		std::vector<std::vector<float>> _sounds;
		std::map<unsigned, float> _playing;
};

}//namespace dlal

#endif
