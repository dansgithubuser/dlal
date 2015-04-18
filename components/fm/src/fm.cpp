#include "fm.hpp"

#include <cmath>
#include <sstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Sonic; }

static float wave(float phase){
	if(phase<0.25f) return 4*phase;
	if(phase<0.75f) return 2-4*phase;
	return -4+4*phase;
}

namespace dlal{

Sonic::Sonic():
	_input(nullptr), _output(nullptr), _ready(false)
{ _oscillators[0]._output=1.0f; }

bool Sonic::ready(){
	if(!_ready) _text="error: sample rate not set";
	else if(!_input) _text="error: input not set";
	else if(!_output) _text="error: output not set";
	return _text.size()==0;
}

void Sonic::addInput(Component* input){
	if(!input->readMidi()){ _text="error: input must provide midi"; return; }
	_input=input;
}

void Sonic::addOutput(Component* output){
	if(!output->readAudio()){ _text="error: output must receive audio"; return; }
	_output=output;
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

std::string* Sonic::readText(){ return &_text; }

void Sonic::clearText(){ _text.clear(); }

void Sonic::sendText(const std::string& text){
	std::stringstream ss(text);
	std::string s;
	ss>>s;
	if(s=="sampleRate"){
		unsigned sampleRate;
		ss>>sampleRate;
		for(unsigned i=0; i<NOTES; ++i) _notes[i].set(i, sampleRate, _oscillators);
		_ready=true;
	}
	else if(s=="test"){
		MidiMessage message;
		message._bytes[0]=0x90;
		message._bytes[1]=0x3c;
		message._bytes[2]=0x7f;
		processMidi(message);
	}
}

std::string Sonic::commands(){ return "sampleRate test"; }

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

void Sonic::Runner::start(){
	_stage=ATTACK;
	_phase=0.0f;
	_volume=0.0f;
	_output=0.0f;
}

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
