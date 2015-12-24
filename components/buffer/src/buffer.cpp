#include "buffer.hpp"

#include <algorithm>

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
}

void Buffer::evaluate(){
	add(_audio.data()+_phase, _samplesPerEvaluation, _outputs);
	phase();
	if(_clearOnEvaluate)
		std::fill_n(_audio.data()+_phase, _samplesPerEvaluation, 0.0f);
}

float* Buffer::audio(){ return _audio.data()+_phase; }

void Buffer::resize(uint64_t period){
	Periodic::resize(period);
	if(_audio.size()<_period) _audio.resize((std::vector<float>::size_type)_period, 0.0f);
}

}//namespace dlal
