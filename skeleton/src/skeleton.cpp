#include "skeleton.hpp"

#include <cstring>
#include <algorithm>

void* dlalBuildSystem(){ return new dlal::System; }

const char* dlalQueryComponent(void* component){
	dlal::Component& c=*(dlal::Component*)component;
	return c.commands().c_str();
}

const char* dlalCommandComponent(void* component, const char* command){
	dlal::Component& c=*(dlal::Component*)component;
	c.clearText();
	c.sendText(command);
	std::string* text=c.readText();
	if(text) return text->c_str();
	return "";
}

const char* dlalAddComponent(void* system, void* component){
	dlal::System& s=*(dlal::System*)system;
	dlal::Component& c=*(dlal::Component*)component;
	c.clearText();
	if(c.ready()) s.addComponent(c);
	std::string* text=c.readText();
	if(text) return text->c_str();
	return "";
}

const char* dlalConnectComponents(void* input, void* output){
	dlal::Component& i=*(dlal::Component*)input;
	dlal::Component& o=*(dlal::Component*)output;
	i.clearText();
	o.clearText();
	i.addOutput(&o);
	o.addInput(&i);
	auto si=i.readText();
	auto so=o.readText();
	static std::string result;
	if(si&&si->size()) result+="input: "+*si+"\n";
	if(so&&so->size()) result+="output: "+*so+"\n";
	return result.c_str();
}

namespace dlal{

//=====System=====//
void System::addComponent(Component& component){
	component._system=this;
	_components.push_back(&component);
}

void System::evaluate(unsigned samples){
	for(auto i:_components) i->evaluate(samples);
}

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
