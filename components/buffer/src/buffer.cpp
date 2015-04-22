#include "buffer.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Buffer; }

static void circularIncrement(unsigned& i, unsigned amount, unsigned size){
	i+=amount;
	if(i+amount>size) i=0;
}

namespace dlal{

Buffer::Buffer(): _i(0) {
	_audio.resize(1);//so readAudio doesn't crash if connecting before resizing
	registerCommand("resize", "size", [&](std::stringstream& ss){
		unsigned size;
		ss>>size;
		_audio.resize(size);
		circularIncrement(_i, 0, size);
		return "";
	});
}

std::string Buffer::readyToEvaluate(){
	if(_audio.size()==1) return "error: must resize";
	return "";
}

void Buffer::evaluate(unsigned samples){
	circularIncrement(_i, samples, _audio.size());
}

float* Buffer::readAudio(){ return _audio.data()+_i; }

}//namespace dlal
