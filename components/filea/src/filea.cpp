#include "filea.hpp"

#include <SFML/Audio.hpp>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Filea; }

namespace dlal{

Filea::Filea(): _i(nullptr), _o(nullptr), _buffer(new std::vector<sf::Int16>) {
	_checkAudio=true;
	addJoinAction([this](System&){
		_audio.resize(_samplesPerEvaluation);
		return "";
	});
	registerCommand("open_read", "<file name>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		if(_i){
			delete (sf::InputSoundFile*)_i;
			_i=nullptr;
		}
		if(fileName=="") return "";
		_i=new sf::InputSoundFile;
		sf::InputSoundFile& file=*(sf::InputSoundFile*)_i;
		if(!file.openFromFile(fileName)) return "error: couldn't open file";
		return "";
	});
	registerCommand("samples", "", [this](std::stringstream&){
		sf::InputSoundFile& file=*(sf::InputSoundFile*)_i;
		std::stringstream ss;
		ss<<file.getSampleCount();
		return ss.str();
	});
	registerCommand("sample_rate", "", [this](std::stringstream&){
		sf::InputSoundFile& file=*(sf::InputSoundFile*)_i;
		std::stringstream ss;
		ss<<file.getSampleRate();
		return ss.str();
	});
	registerCommand("open_write", "<file name>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		if(_o){
			delete (sf::OutputSoundFile*)_o;
			_o=nullptr;
		}
		if(fileName=="") return "";
		_o=new sf::OutputSoundFile;
		sf::OutputSoundFile& file=*(sf::OutputSoundFile*)_o;
		if(!file.openFromFile(fileName, _sampleRate, 1)) return "error: couldn't open file";
		return "";
	});
	registerCommand("close_write", "", [this](std::stringstream&){
		if(_o){
			delete (sf::OutputSoundFile*)_o;
			_o=nullptr;
		}
		return "";
	});
}

Filea::~Filea(){
	delete (sf::InputSoundFile*)_i;
	delete (sf::OutputSoundFile*)_o;
	delete (std::vector<sf::Int16>*)_buffer;
}

void Filea::evaluate(){
	std::vector<sf::Int16>& samples=*(std::vector<sf::Int16>*)_buffer;
	if(_i){
		//read from file
		sf::InputSoundFile& file=*(sf::InputSoundFile*)_i;
		auto x=_samplesPerEvaluation*file.getSampleRate()/_sampleRate;
		if(samples.size()<x) samples.resize(x);
		std::fill(samples.begin(), samples.end(), 0);
		file.read(samples.data(), samples.size());
		for(unsigned i=0; i<_samplesPerEvaluation; ++i){
			auto j=i*file.getSampleRate()/_sampleRate;
			if(j>=samples.size()) break;
			_audio[i]=samples[j]/float(1<<15);
		}
		//write to outputs
		add(_audio.data(), _samplesPerEvaluation, _outputs);
	}
	if(_o){
		//write to file
		if(samples.size()<_audio.size()) samples.resize(_audio.size());
		for(unsigned i=0; i<_audio.size(); ++i)
			samples[i]=_audio[i]*((1<<15)-1);
		sf::OutputSoundFile& file=*(sf::OutputSoundFile*)_o;
		file.write(samples.data(), _audio.size());
		//reset
		std::fill(_audio.begin(), _audio.end(), 0.0f);
	}
}

float* Filea::audio(){ return _audio.data(); }

}//namespace dlal
