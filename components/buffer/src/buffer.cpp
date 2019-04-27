#include "buffer.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>

#include <SFML/Audio.hpp>

#include <obvious.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(Buffer)

namespace dlal{

Buffer::Buffer(): _clearOnEvaluate(false), _repeatSound(false), _pitchSound(false) {
	_checkAudio=true;
	addJoinAction([this](System&){
		if(_audio.size()==0) resize(_period?_period:_samplesPerEvaluation);
		return checkSize(_audio.size());
	});
	registerCommand("clear_on_evaluate", "y/n", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		_clearOnEvaluate=s=="y";
		return "";
	});
	registerCommand("load_raw", "<MIDI note number> <file name>", [this](std::stringstream& ss){
		unsigned note;
		ss>>note;
		std::string fileName;
		ss>>fileName;
		std::ifstream file(fileName.c_str());
		if(!file.good()) return "error: couldn't load file";
		if(_sounds.size()<note+1) _sounds.resize(note+1);
		_sounds[note].clear();
		float f;
		while(file>>f) _sounds[note].push_back(f);
		return "";
	});
	registerCommand("load_sound", "<MIDI note number> <file name>", [this](std::stringstream& ss){
		unsigned note;
		ss>>note;
		std::string fileName;
		ss>>fileName;
		sf::InputSoundFile file;
		if(!file.openFromFile(fileName)) return "error: couldn't open file";
		std::vector<sf::Int16> samples((unsigned)file.getSampleCount());
		file.read(samples.data(), samples.size());
		if(_sounds.size()<note+1) _sounds.resize(note+1);
		_sounds[note].clear();
		_sounds[note].resize(unsigned(file.getDuration().asSeconds()*_sampleRate), 0.0f);
		for(unsigned i=0; i<_sounds[note].size(); ++i){
			auto j=i*file.getSampleRate()/_sampleRate;
			if(j>=file.getSampleCount()) break;
			_sounds[note][i]=samples[j]/float(1<<15);
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
	registerCommand("sound_samples", "<MIDI note number>", [this](std::stringstream& ss){
		unsigned note;
		ss>>note;
		std::stringstream tt;
		tt<<_sounds[note].size();
		return tt.str();
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
	registerCommand("save", "<file name>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		sf::OutputSoundFile file;
		if(!file.openFromFile(fileName, _sampleRate, 1)) return "error: couldn't open file";
		std::vector<sf::Int16> samples;
		for(unsigned i=0; i<_audio.size(); ++i)
			samples.push_back(short(_audio[i]*((1<<15)-1)));
		file.write(samples.data(), samples.size());
		return "";
	});
	registerCommand("serialize_buffer", "", [this](std::stringstream&){
		std::stringstream ss;
		ss<<_sounds;
		return ss.str();
	});
	registerCommand("deserialize_buffer", "<serialized>", [this](std::stringstream& ss){
		ss>>_sounds;
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
					j->audio()[k]+=_sounds[0][unsigned(i->second.sample+k*m)%size]*i->second.volume;
			i->second.sample+=_samplesPerEvaluation*m;
			//ensure repeat-sound logic will work correctly
			auto x=i->second.sample/size;
			if(x>2) i->second.sample-=floor(x-1)*size;
		}
		//soundboarding
		else{
			size=_sounds[i->first].size();
			for(auto j: _outputs){
				//repeat-sound
				if(_repeatSound){
					for(unsigned k=0; k<_samplesPerEvaluation; ++k)
						j->audio()[k]+=_sounds[i->first][unsigned(i->second.sample+k)%size]*i->second.volume;
				}
				//one-shot sound
				else{
					for(unsigned k=0; k<_samplesPerEvaluation&&unsigned(i->second.sample+k)<size; ++k)
						j->audio()[k]+=_sounds[i->first][unsigned(i->second.sample+k)]*i->second.volume;
				}
			}
			i->second.sample+=_samplesPerEvaluation;
		}
		//next
		if(i->second.sample>=size){
			//repeat-sound
			if(_repeatSound){
				i->second.sample-=size;
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
				_playing[bytes[1]]=Playing(bytes[2]/127.0f);
			break;
		default: break;
	}
}

float* Buffer::audio(){ return _audio.data()+_phase; }

std::string Buffer::resize(uint64_t period){
	if(_samplesPerEvaluation){
		auto s=checkSize(period);
		if(isError(s)) return s;
	}
	Periodic::resize(period);
	if(_audio.size()<_period) _audio.resize((std::vector<float>::size_type)_period, 0.0f);
	return "";
}

std::string Buffer::checkSize(uint64_t period){
	if(period<_samplesPerEvaluation)
		return "error: size is less than samplesPerEvaluation";
	if(period%_samplesPerEvaluation)
		return "error: size is not a multiple of samplesPerEvaluation";
	return "";
}

}//namespace dlal
