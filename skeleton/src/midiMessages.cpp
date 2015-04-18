#include "midiMessages.hpp"

#include <cstring>

namespace dlal{

//=====MidiMessage=====//
MidiMessage::MidiMessage(){}

MidiMessage::MidiMessage(const std::vector<uint8_t>& bytes){
	unsigned size=bytes.size();
	if(size>SIZE) size=SIZE;
	memcpy(_bytes, bytes.data(), size);
}

//=====MidiMessages=====//
MidiMessages::MidiMessages(): _size(0) {}

MidiMessage& MidiMessages::operator[](unsigned i){
	return _messages[i];
}

const MidiMessage& MidiMessages::operator[](unsigned i) const{
	return _messages[i];
}

unsigned MidiMessages::size() const{ return _size; }

bool MidiMessages::push_back(const MidiMessage& message){
	if(_size+1>SIZE) return false;
	_messages[_size]=message;
	++_size;
	return true;
}

void MidiMessages::clear(){ _size=0; }

}//namespace dlal
