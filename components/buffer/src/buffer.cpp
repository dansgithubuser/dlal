#include "buffer.hpp"

#include <algorithm>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Buffer; }

static void circularIncrement(unsigned& i, unsigned amount, unsigned size){
	i+=amount;
	if(i+amount>size) i-=size;
}

namespace dlal{

Buffer::Buffer(): _i(0), _clearOnEvaluate(false) {
	_checkAudio=true;
	addJoinAction([this](System&){
		if(_audio.size()<_samplesPerEvaluation)
			return "error: size is less than samplesPerEvaluation";
		if(_audio.size()%_samplesPerEvaluation)
			return "error: size is not a multiple of samplesPerEvaluation";
		return "";
	});
	registerCommand("resize", "size", [this](std::stringstream& ss){
		unsigned size;
		ss>>size;
		_audio.resize(size, 0.0f);
		circularIncrement(_i, 0, size);
		return "";
	});
	registerCommand("clear_on_evaluate", "", [this](std::stringstream& ss){
		_clearOnEvaluate=true;
		return "";
	});
}

void Buffer::evaluate(){
	add(_audio.data()+_i, _samplesPerEvaluation, _outputs);
	circularIncrement(_i, _samplesPerEvaluation, _audio.size());
	if(_clearOnEvaluate)
		std::fill_n(_audio.data()+_i, _samplesPerEvaluation, 0.0f);
}

float* Buffer::audio(){ return _audio.data()+_i; }

}//namespace dlal
