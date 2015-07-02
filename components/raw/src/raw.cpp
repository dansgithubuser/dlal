#include "raw.hpp"

#include <fstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Raw; }

namespace dlal{

Raw::Raw(): _sampleRate(0), _duration(10), _fileName("raw.txt") {
	addJoinAction([this](System& system){
		return system.set(_sampleRate, _log2SamplesPerCallback);
	});
	registerCommand("set", "sampleRate <log2(samples per callback)>",
		[this](std::stringstream& ss){
			ss>>_sampleRate;
			ss>>_log2SamplesPerCallback;
			return "";
		}
	);
	registerCommand("duration", "<duration in ms>",
		[this](std::stringstream& ss){
			ss>>_duration;
			return "";
		}
	);
	registerCommand("file", "<file name>",
		[this](std::stringstream& ss){
			ss>>_fileName;
			return "";
		}
	);
	registerCommand("start", "", [this](std::stringstream& ss)->std::string{
		if(!_system) return "error: must add before starting";
		unsigned samples=1<<_log2SamplesPerCallback;
		_audio.resize(samples);
		std::ofstream file(_fileName.c_str());
		for(unsigned i=0; i<_duration*_sampleRate/1000; i+=samples){
			std::fill_n(_audio.data(), samples, 0.0f);
			_system->evaluate();
			for(unsigned j=0; j<samples; ++j) file<<_audio[j]<<'\n';
		}
		return "";
	});
}

}//namespace dlal
