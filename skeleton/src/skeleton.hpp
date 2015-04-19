#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include "midiMessages.hpp"

#include <string>
#include <vector>
#include <functional>
#include <map>
#include <sstream>

extern "C"{
	//each component implements this
	//return a new instance casted to dlal::Component*
	void* dlalBuildComponent();

	//implemented by skeleton
	void* dlalBuildSystem();
	const char* dlalReadComponent(void* component);
	const char* dlalCommandComponent(void* component, const char* command);
	const char* dlalAddComponent(void* system, void* component);
	const char* dlalConnectComponents(void* input, void* output);
}

namespace dlal{

bool isError(const std::string&);

class Component;

class System{
	public:
		void addComponent(Component& component);
		void evaluate(unsigned samples);
	private:
		std::vector<Component*> _components;
};

class Component{
	public:
		Component(): _system(NULL) {}
		virtual ~Component(){}
		virtual bool ready(){ return true; }
		virtual void addInput(Component*){}
		virtual void addOutput(Component*){}
		virtual void evaluate(unsigned samples){}
		virtual float* readAudio(){ return nullptr; }
		virtual MidiMessages* readMidi(){ return nullptr; }
		virtual std::string* readText(){ return nullptr; }
		std::string sendText(const std::string&);
		System* _system;
	protected:
		typedef std::function<void(std::stringstream&)> Command;
		struct CommandWithParameters{
			Command command;
			std::string parameters;
		};
		void registerCommand(
			const std::string& name,
			const std::string& parameters,
			Command
		);
	private:
		std::map<std::string, CommandWithParameters> _commands;
};

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
