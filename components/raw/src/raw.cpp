#include "raw.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Raw; }

namespace dlal{

Raw::Raw():
	_sampleRate(0), _duration(10), _sample(0), _fileName("raw.txt"), _peak(false)
{
	addJoinAction([this](System& system){
		_audio.resize(1<<_log2SamplesPerCallback, 0.0f);
		_file.open(_fileName.c_str());
		system.set(_sampleRate, _log2SamplesPerCallback);
		_maxSample=_duration*unsigned(_sampleRate)/1000;
		return "";
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
	registerCommand("peak", "<samples>", [this](std::stringstream& ss){
		ss>>_peakWidth;
		_x=Ringbuffer<float>(_peakWidth, 0.0f);
		_peak=true;
		return "";
	});
	registerCommand("start", "", [this](std::stringstream& ss)->std::string{
		if(!_system) return "error: must add before starting";
		auto s=_system->check();
		if(isError(s)) return s;
		const unsigned samples=1<<_log2SamplesPerCallback;
		for(unsigned i=0; i<_maxSample; i+=samples) _system->evaluate();
		return "";
	});
	registerCommand("finish", "", [this](std::stringstream& ss){
		_file.close();
		return "";
	});
}

void Raw::evaluate(){
	if(_sample>=_maxSample) return;
	const unsigned samples=1<<_log2SamplesPerCallback;
	for(unsigned i=0; i<samples; ++i){
		if(_peak){
			_x.write(_audio[i]);
			_file<<_x.max(_peakWidth)<<'\n';
		}
		else _file<<_audio[i]<<'\n';
	}
	_file.flush();
	std::fill_n(_audio.data(), samples, 0.0f);
	_sample+=samples;
}

}//namespace dlal
