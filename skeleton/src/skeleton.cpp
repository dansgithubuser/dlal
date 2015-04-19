#include "skeleton.hpp"

void dlalDemolishComponent(void* component){
	delete (dlal::Component*)component;
}

void* dlalBuildSystem(){ return new dlal::System; }

void dlalDemolishSystem(void* system){
	delete (dlal::System*)system;
}

const char* dlalReadComponent(void* component){
	dlal::Component& c=*(dlal::Component*)component;
	std::string* s=c.readText();
	if(s) return s->c_str();
	else return "";
}

const char* dlalCommandComponent(void* component, const char* command){
	dlal::Component& c=*(dlal::Component*)component;
	static std::string result;
	result=c.sendText(command);
	return result.c_str();
}

const char* dlalAddComponent(void* system, void* component){
	dlal::System& s=*(dlal::System*)system;
	dlal::Component& c=*(dlal::Component*)component;
	if(!c.ready()) return "error: not ready";
	s.addComponent(c);
	return "";
}

static bool connect(dlal::Component& i, dlal::Component& o, bool forward){
	if(forward)
		i.addOutput(&o);
	else
		o.addInput(&i);
	auto si=i.readText();
	auto so=o.readText();
	if(si&&dlal::isError(*si)) return false;
	if(so&&dlal::isError(*so)) return false;
	return true;
}

const char* dlalConnectComponents(void* input, void* output){
	dlal::Component& i=*(dlal::Component*)input;
	dlal::Component& o=*(dlal::Component*)output;
	if(!connect(i, o, true))
		return "error when connecting forward";
	if(!connect(i, o, false))
		return "error when connecting backward";
	return "";
}

namespace dlal{

bool isError(const std::string& s){ return s.compare(0, 7, "error: ")==0; }

//=====System=====//
void System::addComponent(Component& component){
	component._system=this;
	_components.push_back(&component);
}

void System::evaluate(unsigned samples){
	for(auto i:_components) i->evaluate(samples);
}

//=====Component=====//
std::string Component::sendText(const std::string& text){
	std::stringstream ss(text);
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
	_commands[s].command(ss);
	return "";
}

void Component::registerCommand(
	const std::string& name,
	const std::string& parameters,
	Command command
){
	_commands[name]={command, parameters};
}

}//namespace dlal
