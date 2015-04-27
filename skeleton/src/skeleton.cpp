#include "skeleton.hpp"

#include <cstring>
#include <cstdlib>

static dlal::Component* cast(void* p){ return (dlal::Component*)p; }

static char* c_str(const std::string& s){
	char* result=(char*)malloc(s.size()+1);
	result[s.size()]='\0';
	memcpy(result, s.c_str(), s.size());
	return result;
}

void dlalDemolishComponent(void* component){
	delete cast(component);
}

void* dlalBuildSystem(){ return new dlal::System; }

void dlalDemolishSystem(void* system){
	delete (dlal::System*)system;
}

char* dlalCommandComponent(void* component, const char* command){
	return c_str(cast(component)->sendCommand(command));
}

char* dlalConnectInput(void* component, void* input){
	return c_str(cast(component)->addInput(cast(input)));
}

char* dlalConnectOutput(void* component, void* output){
	return c_str(cast(component)->addOutput(cast(output)));
}

char* dlalAddComponent(void* system, void* component){
	return c_str(((dlal::System*)system)->addComponent(*cast(component)));
}

namespace dlal{

bool isError(const std::string& s){ return s.compare(0, 5, "error")==0; }

//=====System=====//
std::string System::addComponent(Component& component){
	std::string result=component.readyToEvaluate();
	if(isError(result)) return result;
	component._system=this;
	_components.push_back(&component);
	return "";
}

void System::evaluate(unsigned samples){
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
