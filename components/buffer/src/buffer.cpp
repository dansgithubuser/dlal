#include "buffer.hpp"

#include <sstream>

static void circularIncrement(unsigned& i, unsigned amount, unsigned size){
	i+=amount;
	if(i+amount>size) i=0;
}

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Buffer; }

namespace dlal{

Buffer::Buffer(): _i(0) {}

bool Buffer::ready(){
	if(!_audio.size()){ _text="error: must resize"; return false; }
	return true;
}

void Buffer::evaluate(unsigned samples){
	circularIncrement(_i, samples, _audio.size());
}

float* Buffer::readAudio(){ return _audio.data()+_i; }

std::string* Buffer::readText(){ return &_text; }

void Buffer::clearText(){ _text.clear(); }

bool Buffer::sendText(const std::string& text){
	std::stringstream ss(text);
	std::string s;
	ss>>s;
	if(s=="resize"){
		unsigned size;
		ss>>size;
		_audio.resize(size);
		circularIncrement(_i, 0, size);
	}
	else return false;
	return true;
}

std::string Buffer::commands(){ return "resize"; }

}//namespace dlal
