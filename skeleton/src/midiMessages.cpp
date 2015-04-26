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

MidiMessages::MidiMessages(const MidiMessage& message): _size(1) {
	_messages[0]=message;
}

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

bool MidiMessages::push_back(const MidiMessages& messages){
	if(_size+messages._size>SIZE) return false;
	memcpy(
		_messages+_size, messages._messages, sizeof(MidiMessage)*messages._size
	);
	_size+=messages._size;
	return true;
}

void MidiMessages::clear(){ _size=0; }

}//namespace dlal
