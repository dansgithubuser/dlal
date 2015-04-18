#include "skeleton.hpp"

void* dlalBuildSystem(){ return new dlal::System; }

const char* dlalQueryComponent(void* component){
	dlal::Component& c=*(dlal::Component*)component;
	return c.commands().c_str();
}

const char* dlalCommandComponent(void* component, const char* command){
	dlal::Component& c=*(dlal::Component*)component;
	c.clearText();
	if(!c.sendText(command)) return "error: unrecognized command";
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

static std::string getConnectResult(
	dlal::Component& i, dlal::Component& o
){
	auto si=i.readText();
	auto so=o.readText();
	std::string result;
	if(si&&si->compare(0, 5, "error")==0) result+="input: "+*si+"\n";
	if(so&&so->compare(0, 5, "error")==0) result+="output: "+*so+"\n";
	return result;
}

const char* dlalConnectComponents(void* input, void* output){
	dlal::Component& i=*(dlal::Component*)input;
	dlal::Component& o=*(dlal::Component*)output;
	i.clearText(); o.clearText();
	i.addOutput(&o);
	static std::string result;
	result=getConnectResult(i, o);
	if(result.size()){
		result="error when connecting forward:\n"+result;
		return result.c_str();
	}
	o.addInput(&i);
	i.clearText(); o.clearText();
	result=getConnectResult(i, o);
	if(result.size()){
		result="error when connecting backward:\n"+result;
		return result.c_str();
	}
	return "";
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

}//namespace dlal
