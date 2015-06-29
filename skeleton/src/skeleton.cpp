#include "skeleton.hpp"

#include <cstring>
#include <cstdlib>
#include <algorithm>

void dlalDemolishComponent(void* component){
	delete dlal::toComponent(component);
}

void* dlalBuildSystem(){ return new dlal::System; }

void dlalDemolishSystem(void* system){
	delete (dlal::System*)system;
}

char* dlalCommandComponent(void* component, const char* command){
	using namespace dlal;
	return toCStr(toComponent(component)->sendCommand(command));
}

char* dlalConnectInput(void* component, void* input){
	using namespace dlal;
	return toCStr(toComponent(component)->addInput(toComponent(input)));
}

char* dlalConnectOutput(void* component, void* output){
	using namespace dlal;
	return toCStr(toComponent(component)->addOutput(toComponent(output)));
}

char* dlalAddComponent(void* system, void* component){
	using namespace dlal;
	return toCStr(((System*)system)->addComponent(*toComponent(component)));
}

namespace dlal{

Component* toComponent(void* p){ return (dlal::Component*)p; }

char* toCStr(const std::string& s){
	char* result=(char*)malloc(s.size()+1);
	result[s.size()]='\0';
	memcpy(result, s.c_str(), s.size());
	return result;
}

bool isError(const std::string& s){ return s.compare(0, 5, "error")==0; }

//=====System=====//
std::string System::addComponent(Component& component){
	std::string result=component.readyToEvaluate();
	if(isError(result)) return result;
	component._system=this;
	_components.push_back(&component);
	return "";
}


std::string System::queueAddComponent(Component& component){
	std::string result=component.readyToEvaluate();
	if(isError(result)) return result;
	component._system=this;
	_componentsToAdd.push_back(&component);
	return "";
}

static bool in(Component* component, const std::vector<Component*>& components){
	return std::find(components.begin(), components.end(), component)!=components.end();
}

std::string System::queueRemoveComponent(Component& component){
	if(!in(&component, _components)) return "error: component was not added";
	_componentsToRemove.push_back(&component);
	return "";
}

void System::evaluate(unsigned samples){
	std::remove_if(_components.begin(), _components.end(), [&](Component* i){
		return in(i, _componentsToRemove);
	});
	for(auto i:_componentsToRemove) i->_system=NULL;
	_componentsToRemove.clear();
	_components.insert(_components.end(), _componentsToAdd.begin(), _componentsToAdd.end());
	_componentsToAdd.clear();
	for(auto i:_components) i->evaluate(samples);
}

//=====Component=====//
std::string Component::sendCommand(const std::string& command){
	std::stringstream ss(command);
	std::string s;
	ss>>s;
	if(!_commands.count(s)){
		std::string result;
		if(s!="help") result+="error: ";
		result+="recognized commands are:\n";
		result+="help\n";
		for(auto i:_commands) result+=i.first+" "+i.second.parameters+"\n";
		return result;
	}
	return _commands[s].command(ss);
}

void Component::registerCommand(
	const std::string& name,
	const std::string& parameters,
	Command command
){
	_commands[name]={command, parameters};
}

}//namespace dlal
