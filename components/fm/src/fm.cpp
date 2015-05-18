#include "fm.hpp"

#include <cmath>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Sonic; }

static float wave(float phase){
	phase-=floor(phase);
	if(phase<0.25f) return 4*phase;
	if(phase<0.75f) return 2-4*phase;
	return -4+4*phase;
}

namespace dlal{

Sonic::Sonic():
	_input(nullptr), _output(nullptr), _sampleRateSet(false)
{
	_oscillators[0]._output=1.0f;
	registerCommand("a", "osc <attack (amplitude per sample)>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._attack;
		return "";
	});
	registerCommand("d", "osc <decay (amplitude per sample)>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._decay;
		return "";
	});
	registerCommand("s", "osc <sustain (amplitude)>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._sustain;
		return "";
	});
	registerCommand("r", "osc <release (amplitude per sample)>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._release;
		return "";
	});
	registerCommand("m", "osc <frequency multiplier>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._frequencyMultiplier;
		return "";
	});
	registerCommand("i", "osc input amplitude", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		unsigned j;
		ss>>j;
		if(j>=OSCILLATORS) return "error: input out of range";
		ss>>_oscillators[i]._inputs[j];
		return "";
	});
	registerCommand("o", "osc <output (amplitude)>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._output;
		return "";
	});
	registerCommand("rate", "<samples per second>", [&](std::stringstream& ss){
		unsigned sampleRate;
		ss>>sampleRate;
		for(unsigned i=0; i<NOTES; ++i) _notes[i].set(i, sampleRate, _oscillators);
		_sampleRateSet=true;
		return "";
	});
	registerCommand("test", "", [&](std::stringstream& ss){
		MidiMessage message;
		message._bytes[0]=0x90;
		message._bytes[1]=0x3c;
		message._bytes[2]=0x7f;
		processMidi(message);
		return "";
	});
}

std::string Sonic::addInput(Component* input){
	if(!input->readMidi()) return "error: input must provide midi";
	_input=input;
	return "";
}

std::string Sonic::addOutput(Component* output){
	if(!output->readAudio()) return "error: output must receive audio";
	_output=output;
	return "";
}

std::string Sonic::readyToEvaluate(){
	if(!_sampleRateSet) return "error: sample rate not set";
	if(!_input) return "error: input not set";
	if(!_output) return "error: output not set";
	return "";
}

void Sonic::evaluate(unsigned samples){
	MidiMessages& messages=*_input->readMidi();
	for(unsigned i=0; i<messages.size(); ++i) processMidi(messages[i]);
	_samples=_output->readAudio();
	for(unsigned i=0; i<NOTES; ++i){
		if(_notes[i]._done) continue;
		for(unsigned j=0; j<samples; ++j){
			_notes[i]._done=true;
			for(unsigned k=0; k<OSCILLATORS; ++k)
				_samples[j]+=_notes[i].update(k, _oscillators);
		}
	}
}

Sonic::Oscillator::Oscillator():
	_attack(0.01f), _decay(0.01f), _sustain(0.5f), _release(0.01f),
	_frequencyMultiplier(1.0f),
	_output(false)
{
	for(unsigned i=0; i<OSCILLATORS; ++i) _inputs[i]=0.0f;
}

bool Sonic::Oscillator::update(Runner& runner) const{
	runner.phase();
	switch(runner._stage){
		case Runner::ATTACK:
			runner._volume+=_attack;
			if(runner._volume>1.0f){
				runner._volume=1.0f;
				runner._stage=Runner::DECAY;
			}
			break;
		case Runner::DECAY:
			runner._volume-=_decay;
			if(runner._volume<_sustain){
				runner._volume=_sustain;
				runner._stage=Runner::SUSTAIN;
			}
			break;
		case Runner::SUSTAIN:
			break;
		case Runner::RELEASE:
			runner._volume-=_release;
			if(runner._volume<0.0f){
				runner._volume=0.0f;
				return true;
			}
			break;
	}
	return _output==0.0f;
}

Sonic::Runner::Runner(): _phase(0.0f), _volume(0.0f), _output(0.0f) {}

void Sonic::Runner::start(){ _stage=ATTACK; }

void Sonic::Runner::phase(){
	_phase+=_step;
	if(_phase>1.0f) _phase-=1.0f;
}

Sonic::Note::Note(): _done(true) {}

void Sonic::Note::set(
	unsigned i, unsigned sampleRate, const Oscillator* oscillators
){
	float step=440.0f*pow(2.0f, (int(i)-69)/12.0f)/sampleRate;
	for(unsigned i=0; i<OSCILLATORS; ++i)
		_runners[i]._step=step*oscillators[i]._frequencyMultiplier;
}

void Sonic::Note::start(float volume, const Oscillator* oscillators){
	for(unsigned i=0; i<OSCILLATORS; ++i) _runners[i].start();
	_volume=volume;
	_done=false;
}

void Sonic::Note::stop(){
	for(unsigned i=0; i<OSCILLATORS; ++i) _runners[i]._stage=Runner::RELEASE;
}

float Sonic::Note::update(unsigned i, const Oscillator* oscillators){
	_done&=oscillators[i].update(_runners[i]);
	float modulatedPhase=_runners[i]._phase;
	for(unsigned j=0; j<OSCILLATORS; ++j)
		modulatedPhase+=_runners[j]._output*oscillators[i]._inputs[j];
	_runners[i]._output=wave(modulatedPhase)*_runners[i]._volume;
	return _runners[i]._output*oscillators[i]._output*_volume;
}

void Sonic::processMidi(const MidiMessage& message){
	uint8_t command=message._bytes[0]&0xf0;
	switch(command){
		case 0x80:
			_notes[message._bytes[1]].stop();
			break;
		case 0x90:
			if(message._bytes[2]==0)
				_notes[message._bytes[1]].stop();
			else
				_notes[message._bytes[1]].start(message._bytes[2]/127.0f, _oscillators);
			break;
		default: break;
	}
}

}//namespace dlal
