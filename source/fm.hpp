#ifndef DLAL_FM_INCLUDED
#define DLAL_FM_INCLUDED

#include <vector>

namespace dlal{

class Sonic{
	public:
		static const unsigned OSCILLATORS=4;
		static const unsigned MIDI_NOTES=128;
		struct Oscillator{
			Oscillator();
			float _attack, _decay, _sustain, _release;
			float _frequencyMultiplier, _inputs[OSCILLATORS];
			float _output;
		};
		Sonic();
		Sonic(float* samples, unsigned sampleRate);
		void processMidi(const std::vector<unsigned char>& message);
		void evaluate(unsigned samplesToEvaluate);
		Oscillator oscillators[OSCILLATORS];
	private:
		struct Runner{
			enum Stage{ ATTACK, DECAY, SUSTAIN, RELEASE };
			void reset(float step);
			Stage _stage;
			float _phase, _step, _volume, _output;
		};
		struct Note{
			Note();
			void set(unsigned i, unsigned sampleRate);
			void start(float volume, const Oscillator* oscillators);
			void stop();
			float _step;
			Runner _runners[OSCILLATORS];
			float _volume;
			unsigned _age;
			bool _done;
			float _previousOutput;
		};
		unsigned _sampleRate;
		float* _samples;
		Note _notes[MIDI_NOTES];
		float _lowness;
};

}//namespace dlal

#endif
