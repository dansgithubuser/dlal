#include "skeleton.hpp"

#include <cstring>
#include <algorithm>

void* dlalBuildSystem(){ return new dlal::System; }

const char* dlalAddComponent(void* system, void* component, const char* name){
	dlal::System& s=*(dlal::System*)system;
	dlal::Component& c=*(dlal::Component*)component;
	std::string n(name);
	return s.addComponent(c, n).c_str();
}

const char* dlalConnectComponents(void* system, const char* nameInput, const char* nameOutput){
	dlal::System& s=*(dlal::System*)system;
	std::string ni(nameInput);
	std::string no(nameOutput);
	return s.connectComponents(ni, no).c_str();
}

const char* dlalCommandComponent(void* system, const char* name, const char* command){
	dlal::System& s=*(dlal::System*)system;
	std::string n(name);
	std::string c(command);
	return s.commandComponent(n, c).c_str();
}

namespace dlal{

//=====System=====//
std::string System::addComponent(Component& component, const std::string& name){
	if(_components.count(name)) return "component name is already used";
	_components[name]=&component;
	_components[name]->_system=this;
	return "";
}

std::string System::connectComponents(const std::string& nameInput, const std::string& nameOutput){
	if(!_components.count(nameInput)) return "couldn't find input component";
	if(!_components.count(nameOutput)) return "couldn't find output component";
	_components[nameOutput]->addInput(_components[nameInput]);
	_components[nameInput]->addOutput(_components[nameOutput]);
	return "";
}

std::string System::commandComponent(const std::string& name, const std::string& command){
	if(!_components.count(name)) return "couldn't find component";
	_components[name]->sendText(command.c_str());
	const std::string* result=_components[name]->readText();
	if(result) return *result;
	return "";
}

void System::evaluate(unsigned samples){
	for(auto i:_components) i.second->evaluate(samples);
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
