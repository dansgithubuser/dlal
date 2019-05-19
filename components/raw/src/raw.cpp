#include "raw.hpp"

#include <iostream>

DLAL_BUILD_COMPONENT_DEFINITION(Raw)

namespace dlal{

Raw::Raw():
	_sampleRate(0), _duration(10), _sample(0), _fileName("raw.txt"),
	_doFile(true), _peak(false), _print(false)
{
	addJoinAction([this](System& system){
		_audio.resize(1<<_log2SamplesPerEvaluation, 0.0f);
		_file.open(_fileName.c_str());
		system.set(_sampleRate, _log2SamplesPerEvaluation);
		_maxSample=_duration*_sampleRate/1000;
		return "";
	});
	registerCommand("set", "sampleRate <log2(samples per evaluation)>",
		[this](std::stringstream& ss){
			ss>>_sampleRate;
			ss>>_log2SamplesPerEvaluation;
			return "";
		}
	);
	registerCommand("duration", "<duration in ms>",
		[this](std::stringstream& ss){
			ss>>_duration;
			if(_system) _maxSample=_duration*_sampleRate/1000;
			return "";
		}
	);
	registerCommand("file", "<file name>",
		[this](std::stringstream& ss){
			ss>>_fileName;
			return "";
		}
	);
	registerCommand("peak", "<samples>", [this](std::stringstream& ss){
		ss>>_peakWidth;
		_x=Ringbuffer<float>(_peakWidth, 0.0f);
		_peak=true;
		return "";
	});
	registerCommand("set_print", "y/n", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		_print=s=="y";
		return "";
	});
	registerCommand("do_file", "y/n", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		_doFile=s=="y";
		return "";
	});
	registerCommand("start", "pause", [this](std::stringstream& ss)->std::string{
		int pause=0;
		ss>>pause;
		if(!_system) return "error: must add before starting";
		auto s=_system->prep();
		if(isError(s)) return s;
		const unsigned samples=1<<_log2SamplesPerEvaluation;
		int j=0;
		if(pause) return "";
		for(uint64_t i=0; i<_maxSample; i+=samples){
			if(_print){
				++j;
				j%=100;
				if(!j) std::cout<<i<<"/"<<_maxSample<<"\n";
			}
			_system->evaluate();
		}
		return "";
	});
	registerCommand("evaluate", "", [this](std::stringstream&)->std::string{
		_system->evaluate();
		return "";
	});
	registerCommand("finish", "", [this](std::stringstream& ss){
		_file.close();
		return "";
	});
}

void Raw::evaluate(){
	if(_sample>=_maxSample) return;
	const unsigned samples=1<<_log2SamplesPerEvaluation;
	for(unsigned i=0; i<samples; ++i){
		if(_peak){
			_x.write(_audio[i]);
			_file<<_x.max(_peakWidth)<<'\n';
		}
		else if(_doFile) _file<<_audio[i]<<'\n';
	}
	_file.flush();
	std::fill_n(_audio.data(), samples, 0.0f);
	_sample+=samples;
}

}//namespace dlal
