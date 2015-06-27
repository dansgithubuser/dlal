#include "raw.hpp"

#include <fstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Raw; }

namespace dlal{

Raw::Raw(): _sampleRate(0), _output(1), _duration(10), _fileName("raw.txt") {
	registerCommand("set", "sampleRate <log2(samples per callback)>",
		[&](std::stringstream& ss){
			ss>>_sampleRate;
			ss>>_log2SamplesPerCallback;
			return "";
		}
	);
	registerCommand("duration", "<duration in ms>",
		[&](std::stringstream& ss){
			ss>>_duration;
			return "";
		}
	);
	registerCommand("file", "<file name>",
		[&](std::stringstream& ss){
			ss>>_fileName;
			return "";
		}
	);
	registerCommand("start", "", [&](std::stringstream& ss)->std::string{
		unsigned samples=1<<_log2SamplesPerCallback;
		_output.resize(samples);
		std::ofstream file(_fileName.c_str());
		for(unsigned i=0; i<_duration*_sampleRate/1000; i+=samples){
			_system->evaluate(samples);
			for(unsigned j=0; j<samples; ++j) file<<_output[j]<<'\n';
		}
		return "";
	});
}

std::string Raw::addInput(Component* component){
	if(std::count(_inputs.begin(), _inputs.end(), component))
		return "input already added";
	_inputs.push_back(component);
	return "";
}

std::string Raw::readyToEvaluate(){
	if(!_sampleRate)
		return "error: must set sample rate and log2 samples per callback";
	return "";
}

void Raw::evaluate(unsigned samples){
	for(unsigned i=0; i<samples; ++i) _output[i]=0.0f;
	for(unsigned j=0; j<_inputs.size(); ++j){
		float* audio=_inputs[j]->readAudio();
		if(!audio) continue;
		for(unsigned i=0; i<samples; ++i) _output[i]+=audio[i];
	}
}

float* Raw::readAudio(){ return _output.data(); }

}//namespace dlal
