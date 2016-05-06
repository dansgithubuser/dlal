#include "buffer.hpp"

#include <algorithm>
#include <cmath>

#include <SFML/Audio.hpp>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Buffer; }

namespace dlal{

Buffer::Buffer(): _clearOnEvaluate(false), _repeatSound(false), _pitchSound(false) {
	_checkAudio=true;
	addJoinAction([this](System&){
		if(_audio.size()<_samplesPerEvaluation){
			if(_audio.empty()) resize(_samplesPerEvaluation);
			else return "error: size is less than samplesPerEvaluation";
		}
		if(_audio.size()%_samplesPerEvaluation)
			return "error: size is not a multiple of samplesPerEvaluation";
		return "";
	});
	registerCommand("clear_on_evaluate", "y/n", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		_clearOnEvaluate=s=="y";
		return "";
	});
	registerCommand("load_sound", "<MIDI note number> <file name>", [this](std::stringstream& ss){
		unsigned note;
		ss>>note;
		std::string fileName;
		ss>>fileName;
		sf::SoundBuffer soundBuffer;
		if(!soundBuffer.loadFromFile(fileName)) return "error: couldn't load file";
		if(_sounds.size()<note+1) _sounds.resize(note+1);
		_sounds[note].clear();
		_sounds[note].resize(unsigned(soundBuffer.getDuration().asSeconds()*_sampleRate), 0.0f);
		for(unsigned i=0; i<_sounds[note].size(); ++i){
			auto j=i*soundBuffer.getSampleRate()/_sampleRate;
			if(j>=soundBuffer.getSampleCount()) break;
			_sounds[note][i]=soundBuffer.getSamples()[j]/float(1<<15);
		}
		return "";
	});
	registerCommand("read_sound", "<MIDI note number> samples", [this](std::stringstream& ss){
		unsigned note;
		ss>>note;
		if(_sounds.size()<note+1) _sounds.resize(note+1);
		_sounds[note].clear();
		float s;
		while(ss>>s) _sounds[note].push_back(s);
		return "";
	});
	registerCommand("repeat_sound", "y/n", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		_repeatSound=s=="y";
		return "";
	});
	registerCommand("pitch_sound", "y/n", [this](std::stringstream& ss){
		if(_sounds.empty()) return "error: no sound to pitch\n";
		if(_sounds[0].empty()) return "error: sound to pitch can't be empty\n";
		std::string s;
		ss>>s;
		_pitchSound=s=="y";
		return "";
	});
}

void Buffer::evaluate(){
	//recorded
	add(_audio.data()+_phase, _samplesPerEvaluation, _outputs);
	//sounds
	for(auto i=_playing.begin(); i!=_playing.end(); /*nothing*/){
		unsigned size;
		//pitch-sound
		if(_pitchSound){
			size=_sounds[0].size();
			float m=pow(2.0f, i->first/12.0f);
			for(auto j: _outputs)
				for(unsigned k=0; k<_samplesPerEvaluation; ++k)
					j->audio()[k]+=_sounds[0][unsigned(i->second+k*m)%size];
			i->second+=_samplesPerEvaluation*m;
			//ensure repeat-sound logic will work correctly
			auto x=i->second/size;
			if(x>2) i->second-=floor(x-1)*size;
		}
		//soundboarding
		else{
			size=_sounds[i->first].size();
			for(auto j: _outputs){
				//repeat-sound
				if(_repeatSound){
					for(unsigned k=0; k<_samplesPerEvaluation; ++k)
						j->audio()[k]+=_sounds[i->first][unsigned(i->second+k)%size];
				}
				//one-shot sound
				else{
					for(unsigned k=0; k<_samplesPerEvaluation&&unsigned(i->second+k)<size; ++k)
						j->audio()[k]+=_sounds[i->first][unsigned(i->second+k)];
				}
			}
			i->second+=_samplesPerEvaluation;
		}
		//next
		if(i->second>=size){
			//repeat-sound
			if(_repeatSound){
				i->second-=size;
				++i;
			}
			//one-shot sound
			else _playing.erase(i++);
		}
		else ++i;
	}
	//phasing
	phase();
	//clear-on-evaluate
	if(_clearOnEvaluate)
		std::fill_n(_audio.data()+_phase, _samplesPerEvaluation, 0.0f);
}

void Buffer::midi(const uint8_t* bytes, unsigned size){
	if(!size) return;
	uint8_t command=bytes[0]&0xf0;
	switch(command){
		case 0x80:
			if(size<2) break;
			_playing.erase(bytes[1]);
			break;
		case 0x90:
			if(size<3) break;
			if(bytes[2]==0)
				_playing.erase(bytes[1]);
			else if(_pitchSound||bytes[1]<_sounds.size())
				_playing[bytes[1]]=0.0f;
			break;
		default: break;
	}
}

float* Buffer::audio(){ return _audio.data()+_phase; }

void Buffer::resize(uint64_t period){
	Periodic::resize(period);
	if(_audio.size()<_period) _audio.resize((std::vector<float>::size_type)_period, 0.0f);
}

}//namespace dlal
