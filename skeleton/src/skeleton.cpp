#include "skeleton.hpp"

void dlalDemolishComponent(void* component){
	delete (dlal::Component*)component;
}

void* dlalBuildSystem(){ return new dlal::System; }

void dlalDemolishSystem(void* system){
	delete (dlal::System*)system;
}

const char* dlalCommandComponent(void* component, const char* command){
	static std::string result;
	result=((dlal::Component*)component)->sendCommand(command);
	return result.c_str();
}

const char* dlalConnectInput(void* component, void* input){
	static std::string result;
	result=((dlal::Component*)component)->addInput((dlal::Component*)input);
	return result.c_str();
}

const char* dlalConnectOutput(void* component, void* output){
	static std::string result;
	result=((dlal::Component*)component)->addOutput((dlal::Component*)output);
	return result.c_str();
}

const char* dlalAddComponent(void* system, void* component){
	static std::string result;
	result=((dlal::System*)system)->addComponent(*(dlal::Component*)component);
	return result.c_str();
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
