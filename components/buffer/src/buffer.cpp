#include "buffer.hpp"

static void circularIncrement(unsigned& i, unsigned amount, unsigned size){
	i+=amount;
	if(i+amount>size) i=0;
}

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Buffer; }

namespace dlal{

Buffer::Buffer(): _i(0) {
	_audio.resize(1);
	registerCommand("resize", "size", [&](std::stringstream& ss){
		unsigned size;
		ss>>size;
		_audio.resize(size);
		circularIncrement(_i, 0, size);
		_text="";
	});
}

bool Buffer::ready(){
	if(!_audio.size()){ _text="error: must resize"; return false; }
	_text="";
	return true;
}

void Buffer::evaluate(unsigned samples){
	circularIncrement(_i, samples, _audio.size());
}

float* Buffer::readAudio(){ return _audio.data()+_i; }

std::string* Buffer::readText(){ return &_text; }

}//namespace dlal
