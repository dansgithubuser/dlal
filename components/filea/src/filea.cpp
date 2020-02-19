#include "filea.hpp"

#include <SFML/Audio.hpp>

#include <obvious.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(Filea)

namespace dlal{

Filea::Filea(): _i(nullptr), _o(nullptr), _buffer(new std::vector<sf::Int16>),
	_volume(1.0f), _desiredVolume(1.0f), _deltaVolume(0.0f), _sample(0), _queue(16)
{
	_checkAudio=true;
	addJoinAction([this](System&){
		_audio.resize(_samplesPerEvaluation);
		return "";
	});
	registerCommand("open_read", "<file name>", [this](std::stringstream& ss){
		ss>>std::ws;
		std::string fileName;
		std::getline(ss, fileName);
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
	registerCommand("read", "<file name>", [this](std::stringstream& ss)->std::string{
		ss>>std::ws;
		std::string fileName;
		std::getline(ss, fileName);
		sf::InputSoundFile file;
		if(!file.openFromFile(fileName)) return "error: couldn't open file";
		//read file
		std::vector<sf::Int16> samples(file.getSampleCount());
		file.read(samples.data(), samples.size());
		//handle relative sample rates
		static std::vector<float> buffer;
		buffer.resize(size_t(file.getSampleCount()*_sampleRate/file.getSampleRate()));
		for(size_t i=0; i<buffer.size(); ++i){
			unsigned j=i*file.getSampleRate()/_sampleRate;
			if(j>=file.getSampleCount()) break;
			buffer[i]=samples[j]/float(1<<15);
		}
		return ::str((void*)buffer.data(), buffer.size());
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
		ss>>std::ws;
		std::string fileName;
		std::getline(ss, fileName);
		if(_o){
			delete (sf::OutputSoundFile*)_o;
			_o=nullptr;
		}
		if(fileName=="") return "";
		_o=new sf::OutputSoundFile;
		sf::OutputSoundFile& file=*(sf::OutputSoundFile*)_o;
		if(!file.openFromFile(fileName, _sampleRate, 1)) return "error: couldn't open file";
		threadStart();
		return "";
	});
	registerCommand("close_write", "", [this](std::stringstream&){
		if(_o){
			threadEnd();
			delete (sf::OutputSoundFile*)_o;
			_o=nullptr;
		}
		return "";
	});
	registerCommand("write_on_midi", "[enable, default 1]", [this](std::stringstream& ss){
		int enable=1;
		ss>>enable;
		_writeOnMidi=(bool)enable;
		_shouldWrite=!_writeOnMidi;
		return "";
	});
	registerCommand("set_volume", "volume", [this](std::stringstream& ss){
		ss>>_volume;
		return "";
	});
	registerCommand("fade", "volume <duration in seconds>", [this](std::stringstream& ss){
		ss>>_desiredVolume;
		float duration;
		ss>>duration;
		_deltaVolume=(_desiredVolume-_volume)/duration/_sampleRate*_samplesPerEvaluation;
		return "";
	});
	registerCommand("loop_crossfade", "<duration in seconds>", [this](std::stringstream& ss){
		float duration;
		ss>>duration;
		unsigned samples=(unsigned)(duration*_sampleRate);
		sf::InputSoundFile& file=*(sf::InputSoundFile*)_i;
		std::vector<sf::Int16> v(samples);
		file.read(v.data(), samples);
		_loop_crossfade.resize(samples);
		for(unsigned i=0; i<samples; ++i) _loop_crossfade[i]=v[i]/float(1<<15);
		return "";
	});
}

Filea::~Filea(){
	threadEnd();
	delete (sf::InputSoundFile*)_i;
	delete (sf::OutputSoundFile*)_o;
	delete (std::vector<sf::Int16>*)_buffer;
}

static float linear(float a, float b, float bness){
	return a*(1-bness)+b*bness;
}

void Filea::evaluate(){
	std::vector<sf::Int16>& samples=*(std::vector<sf::Int16>*)_buffer;
	if(_volume!=0.0f&&_i){
		//read from file
		sf::InputSoundFile& file=*(sf::InputSoundFile*)_i;
		auto x=_samplesPerEvaluation*file.getSampleRate()/_sampleRate;
		if(samples.size()<x) samples.resize(x);
		std::fill(samples.begin(), samples.end(), 0);
		if(auto r=file.read(samples.data(), samples.size())<samples.size()){
			file.seek(_loop_crossfade.size());
			file.read(samples.data()+r, samples.size()-r);
		}
		for(unsigned i=0; i<_samplesPerEvaluation; ++i){
			unsigned j=i*file.getSampleRate()/_sampleRate;
			if(j>=samples.size()) break;
			auto l=_loop_crossfade.size()/2;
			if(_sample<l){
				unsigned k=(unsigned)(l+_sample);
				_audio[i]=_volume*linear(
					_loop_crossfade[k], samples[j]/float(1<<15), 1.0f*_sample/l
				);
			}
			else if(file.getSampleCount()-_sample<l){
				unsigned k=(unsigned)(l-(file.getSampleCount()-_sample));
				_audio[i]=_volume*linear(
					_loop_crossfade[k], samples[j]/float(1<<15), (1.0f*file.getSampleCount()-_sample)/l
				);
			}
			else
				_audio[i]=_volume*samples[j]/float(1<<15);
			++_sample;
			_sample%=file.getSampleCount();
		}
		//write to outputs
		add(_audio.data(), _samplesPerEvaluation, _outputs);
	}
	if(_o&&_shouldWrite){
		_queue.write(_audio.data(), _audio.size());
		std::fill(_audio.begin(), _audio.end(), 0.0f);
	}
	//volume
	_volume+=_deltaVolume;
	if(
		(_deltaVolume<0.0f&&_volume<_desiredVolume)
		||
		(_deltaVolume>0.0f&&_volume>_desiredVolume)
	){
		_volume=_desiredVolume;
		_deltaVolume=0.0f;
	}
}

void Filea::midi(const uint8_t* bytes, unsigned size){
	if(_writeOnMidi&&size==3){
		switch(bytes[0]>>4){
			case 9:
				if(bytes[2])
					_shouldWrite=true;
				else
					_shouldWrite=false;
				break;
			case 8:
				_shouldWrite=false;
				break;
			default: break;
		}
	}
}

float* Filea::audio(){ return _audio.data(); }

void Filea::threadStart(){
	_thread=std::thread([this](){
		std::vector<sf::Int16> samples;
		bool done=false;
		while(!done){
			std::this_thread::sleep_for(std::chrono::milliseconds(1));
			if(_quit) done=true;
			float f;
			while(_queue.read(f, true)){
				if(f<-1.0f) f=-1.0f;
				else if(f>1.0f) f=1.0f;
				samples.push_back(sf::Int16(f*((1<<15)-1)));
			}
			sf::OutputSoundFile& file=*(sf::OutputSoundFile*)_o;
			file.write(samples.data(), samples.size());
			samples.clear();
		}
	});
}

void Filea::threadEnd(){
	_quit=true;
	_thread.join();
}

}//namespace dlal
