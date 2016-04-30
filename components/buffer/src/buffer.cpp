#include "buffer.hpp"

#include <algorithm>

#include <SFML/Audio.hpp>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Buffer; }

namespace dlal{

Buffer::Buffer(): _clearOnEvaluate(false) {
	_checkAudio=true;
	addJoinAction([this](System&){
		if(_audio.size()<_samplesPerEvaluation)
			return "error: size is less than samplesPerEvaluation";
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
	registerCommand("load_sound", "<file name> <MIDI note number>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		unsigned note;
		ss>>note;
		sf::SoundBuffer soundBuffer;
		if(!soundBuffer.loadFromFile(fileName)) return "error: couldn't load file";
		if(_sounds.size()<note+1) _sounds.resize(note+1);
		_sounds[note].clear();
		auto size=unsigned(soundBuffer.getDuration().asSeconds()*_sampleRate);
		size=size/_samplesPerEvaluation*_samplesPerEvaluation+_samplesPerEvaluation;
		_sounds[note].resize(size, 0.0f);
		for(unsigned i=0; i<_sounds[note].size(); ++i){
			auto j=i*soundBuffer.getSampleRate()/_sampleRate;
			if(j>=soundBuffer.getSampleCount()) break;
			_sounds[note][i]=soundBuffer.getSamples()[j]/float(1<<15);
		}
		return "";
	});
}

void Buffer::evaluate(){
	add(_audio.data()+_phase, _samplesPerEvaluation, _outputs);
	for(auto i=_playing.begin(); i!=_playing.end(); /*nothing*/){
		add(_sounds[i->first].data()+i->second, _samplesPerEvaluation, _outputs);
		i->second+=_samplesPerEvaluation;
		if(i->second>=_sounds[i->first].size()) _playing.erase(i++);
		else ++i;
	}
	phase();
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
			else if(bytes[1]<_sounds.size())
				_playing[bytes[1]]=0;
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
