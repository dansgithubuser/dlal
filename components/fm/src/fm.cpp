#include "fm.hpp"

#include <cmath>
#include <fstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Sonic; }

static float wave(float phase){
	return sin(phase*2*3.14159f);
}

namespace dlal{

Sonic::Sonic(): _frequencyMultiplier(1.0f) {
	_oscillators[0]._output=1.0f;
	_checkAudio=true;
	addJoinAction([this](System&){ update(); return ""; });
	registerCommand("a", "osc <attack (amplitude per sample)>", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._attack;
		return "";
	});
	registerCommand("d", "osc <decay (amplitude per sample)>", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._decay;
		return "";
	});
	registerCommand("s", "osc <sustain (amplitude)>", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._sustain;
		return "";
	});
	registerCommand("r", "osc <release (amplitude per sample)>", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._release;
		return "";
	});
	registerCommand("m", "osc <frequency multiplier>", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._frequencyMultiplier;
		update();
		return "";
	});
	registerCommand("i", "osc input amplitude", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		unsigned j;
		ss>>j;
		if(j>=OSCILLATORS) return "error: input out of range";
		ss>>_oscillators[i]._inputs[j];
		return "";
	});
	registerCommand("o", "osc <output (amplitude)>", [this](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=OSCILLATORS) return "error: osc out of range";
		ss>>_oscillators[i]._output;
		return "";
	});
	registerCommand("frequency_multiplier", "<frequency multiplier>", [this](std::stringstream& ss){
		ss>>_frequencyMultiplier;
		return "";
	});
	registerCommand("test", "", [this](std::stringstream& ss){
		uint8_t m[3]={ 0x90, 0x3c, 0x7f };
		midi(m, sizeof(m));
		return "";
	});
	registerCommand("save", "<file name, or i to return contents of would-be file>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		std::ofstream file;
		std::stringstream internal;
		std::ostream* stream=&internal;
		if(fileName!="i"){
			file.open(fileName.c_str());
			if(!file.good()) return std::string("error: couldn't open file");
			stream=&file;
		}
		for(unsigned i=0; i<OSCILLATORS; ++i){
			*stream<<"a "<<i<<" "<<_oscillators[i]._attack<<"\n";
			*stream<<"d "<<i<<" "<<_oscillators[i]._decay<<"\n";
			*stream<<"s "<<i<<" "<<_oscillators[i]._sustain<<"\n";
			*stream<<"r "<<i<<" "<<_oscillators[i]._release<<"\n";
			*stream<<"m "<<i<<" "<<_oscillators[i]._frequencyMultiplier<<"\n";
			for(unsigned j=0; j<OSCILLATORS; ++j)
				*stream<<"i "<<i<<" "<<j<<" "<<_oscillators[i]._inputs[j]<<"\n";
			*stream<<"o "<<i<<" "<<_oscillators[i]._output<<"\n";
		}
		return internal.str();
	});
	registerCommand("load", "<file name>", [this](std::stringstream& ss){
		std::string s, result;
		ss>>s;
		std::ifstream file(s.c_str());
		if(!file.good()) return std::string("error: couldn't open file");
		bool error=false;
		while(std::getline(file, s)){
			s=command(s);
			if(isError(s)) error=true;
			result+=s+"\n";
		}
		if(error) result="error: a load command failed\n"+result;
		return result;
	});
	for(unsigned i=0; i<OSCILLATORS; ++i){
		std::stringstream ss;
		ss<<i;
		std::string s=ss.str();
		_nameToControl["a"+s]=&_oscillators[i]._attack;
		_nameToControl["d"+s]=&_oscillators[i]._decay;
		_nameToControl["s"+s]=&_oscillators[i]._sustain;
		_nameToControl["r"+s]=&_oscillators[i]._release;
		_nameToControl["m"+s]=&_oscillators[i]._frequencyMultiplier;
		for(unsigned j=0; j<OSCILLATORS; ++j){
			std::stringstream tt;
			tt<<j;
			std::string t=tt.str();
			_nameToControl["i"+s+t]=&_oscillators[i]._inputs[j];
		}
		_nameToControl["o"+s]=&_oscillators[i]._output;
	}
}

void Sonic::evaluate(){
	for(unsigned i=0; i<NOTES; ++i){
		if(_notes[i]._done) continue;
		for(unsigned j=0; j<_samplesPerEvaluation; ++j){
			_notes[i]._done=true;
			for(unsigned k=0; k<OSCILLATORS; ++k)
				for(auto output: _outputs)
					output->audio()[j]+=_notes[i].update(k, _oscillators, _frequencyMultiplier);
		}
	}
}

void Sonic::midi(const uint8_t* bytes, unsigned size){
	MidiControllee::midi(bytes, size);
	if(!size) return;
	uint8_t command=bytes[0]&0xf0;
	switch(command){
		case 0x80:
			if(size<2) break;
			_notes[bytes[1]].stop();
			break;
		case 0x90:
			if(size<3) break;
			if(bytes[2]==0)
				_notes[bytes[1]].stop();
			else
				_notes[bytes[1]].start(bytes[2]/127.0f, _oscillators);
			break;
		default: break;
	}
}

Sonic::Oscillator::Oscillator():
	_attack(0.01f), _decay(0.01f), _sustain(0.5f), _release(0.01f),
	_frequencyMultiplier(1.0f),
	_output(false)
{
	for(unsigned i=0; i<OSCILLATORS; ++i) _inputs[i]=0.0f;
}

bool Sonic::Oscillator::update(Runner& runner, float frequencyMultiplier) const{
	runner.phase(frequencyMultiplier);
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

Sonic::Runner::Runner(): _phase(0.0f), _output(0.0f) {}

void Sonic::Runner::start(){
	_stage=ATTACK;
	_volume=0.0f;
}

void Sonic::Runner::phase(float frequencyMultiplier){
	_phase+=_step*frequencyMultiplier;
	if(_phase>1.0f) _phase-=1.0f;
}

Sonic::Note::Note(): _done(true) {}

void Sonic::Note::set(
	unsigned i, unsigned sampleRate, const Oscillator* oscillators
){
	if(sampleRate==0) return;
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

float Sonic::Note::update(unsigned i, const Oscillator* oscillators, float frequencyMultiplier){
	_done&=oscillators[i].update(_runners[i], frequencyMultiplier);
	float modulatedPhase=_runners[i]._phase;
	for(unsigned j=0; j<OSCILLATORS; ++j)
		modulatedPhase+=_runners[j]._output*oscillators[i]._inputs[j];
	_runners[i]._output=wave(modulatedPhase)*_runners[i]._volume;
	return _runners[i]._output*oscillators[i]._output*_volume;
}

void Sonic::update(){
	for(unsigned i=0; i<NOTES; ++i) _notes[i].set(i, _sampleRate, _oscillators);
}

}//namespace dlal
