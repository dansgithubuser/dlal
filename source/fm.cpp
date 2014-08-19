#include "fm.hpp"

#include <cmath>

static float wave(float phase){
	if(phase>1.0f) phase-=1.0f;
	else if(phase<0.0f) phase+=1.0f;
	if(phase<0.25f) return 4*phase;
	if(phase<0.75f) return 2-4*phase;
	return -4+4*phase;
}

namespace dlal{

Sonic::Oscillator::Oscillator():
	_attack(0.01f), _decay(0.01f), _sustain(0.5f), _release(0.01f),
	_frequencyMultiplier(1.0f),
	_output(false)
{
	for(unsigned i=0; i<OSCILLATORS; ++i) _inputs[i]=0.0f;
}

Sonic::Sonic(){}

Sonic::Sonic(float* samples, unsigned sampleRate):
	_samples(samples), _sampleRate(sampleRate)
{
	oscillators[0]._output=1.0f;
	for(unsigned i=0; i<MIDI_NOTES; ++i)
		_notes[i].set(i, sampleRate);
}

void Sonic::processMidi(const std::vector<unsigned char>& message){
	unsigned char command=message[0]&0xf0;
	switch(command){
		case 0x80:
			_notes[message[1]].stop();
			break;
		case 0x90:
			if(message[2]==0) _notes[message[1]].stop();
			else _notes[message[1]].start(message[2]/127.0f, oscillators);
			break;
		default: break;
	}
}

void Sonic::evaluate(unsigned samplesToEvaluate){
	for(unsigned i=0; i<MIDI_NOTES; ++i){
		if(_notes[i]._done) continue;
		for(unsigned j=0; j<samplesToEvaluate; ++j){
			++_notes[i]._age;
			_notes[i]._done=true;
			for(unsigned k=0; k<OSCILLATORS; ++k){
				//update runner phase
				_notes[i]._runners[k]._phase+=_notes[i]._runners[k]._step;
				if(_notes[i]._runners[k]._phase>1.0f) _notes[i]._runners[k]._phase-=1.0f;
				//update runner volume and stage
				switch(_notes[i]._runners[k]._stage){
					case Runner::ATTACK:
						_notes[i]._runners[k]._volume+=oscillators[k]._attack;
						if(_notes[i]._runners[k]._volume>1){
							_notes[i]._runners[k]._volume=1;
							_notes[i]._runners[k]._stage=Runner::DECAY;
						}
						if(oscillators[k]._output>0.0f) _notes[i]._done=false;
						break;
					case Runner::DECAY:
						_notes[i]._runners[k]._volume-=oscillators[k]._decay;
						if(_notes[i]._runners[k]._volume<oscillators[k]._sustain){
							_notes[i]._runners[k]._volume=oscillators[k]._sustain;
							_notes[i]._runners[k]._stage=Runner::SUSTAIN;
						}
						if(oscillators[k]._output>0.0f) _notes[i]._done=false;
						break;
					case Runner::SUSTAIN:
						if(oscillators[k]._output>0.0f) _notes[i]._done=false;
						break;
					case Runner::RELEASE:
						_notes[i]._runners[k]._volume-=oscillators[k]._release;
						if(_notes[i]._runners[k]._volume<0) _notes[i]._runners[k]._volume=0;
						else if(oscillators[k]._output) _notes[i]._done=false;
						break;
					default: break;
				}
				//update output
				float modulatedPhase=_notes[i]._runners[k]._phase;
				for(unsigned l=0; l<OSCILLATORS; ++l)
					modulatedPhase+=_notes[i]._runners[l]._output*oscillators[k]._inputs[l];
				_notes[i]._runners[k]._output=wave(modulatedPhase)*_notes[i]._runners[k]._volume;
				//add contribution to current sample
				_samples[j]+=_notes[i]._runners[k]._output*oscillators[k]._output*_notes[i]._volume;
			}//for(unsigned k=0; k<OSCILLATORS; ++k)
		}//for(unsigned j=0; j<samplesToEvaluate; ++j)
	}//for(unsigned i=0; i<MIDI_NOTES; ++i)
}

void Sonic::Runner::reset(float step){
	_stage=ATTACK;
	_phase=0.0f;
	_step=step;
	_volume=0.0f;
	_output=0.0f;
}

Sonic::Note::Note(): _done(true) {}

void Sonic::Note::set(unsigned i, unsigned sampleRate){
	_step=440.0f*pow(2.0f, (int(i)-69)/12.0f)/sampleRate;
}

void Sonic::Note::start(float volume, const Oscillator* oscillators){
	for(unsigned i=0; i<OSCILLATORS; ++i)
		_runners[i].reset(_step*oscillators[i]._frequencyMultiplier);
	_volume=volume;
	_age=0;
	_done=false;
}

void Sonic::Note::stop(){
	for(unsigned i=0; i<OSCILLATORS; ++i)
		_runners[i]._stage=Runner::RELEASE;
}

}//namespace dlal
