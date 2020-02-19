#ifndef DLAL_FILEA_INCLUDED
#define DLAL_FILEA_INCLUDED

#include <skeleton.hpp>

#include <thread>

namespace dlal{

class Filea: public MultiOut, public SamplesPerEvaluationGetter, public SampleRateGetter{
	public:
		Filea();
		~Filea();
		std::string type() const override { return "filea"; }
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
		float* audio() override;
		bool hasAudio() override { return true; }
	private:
		void threadStart();
		void threadEnd();
		std::vector<float> _audio;
		void* _i;
		void* _o;
		void* _buffer;
		Queue<float> _queue;
		std::thread _thread;
		bool _quit=false;
		float _volume, _desiredVolume, _deltaVolume;
		std::vector<float> _loop_crossfade;
		uint64_t _sample;
		bool _writeOnMidi=false, _shouldWrite=true;
};

}//namespace dlal

#endif
