#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include "midiMessages.hpp"

#include <string>
#include <vector>
#include <functional>
#include <map>
#include <sstream>

#ifdef _MSC_VER
	#define DLAL __declspec(dllexport)
#else
	#define DLAL
#endif

extern "C"{
	//each component implements this
	//return a new instance casted to dlal::Component*
	DLAL void* dlalBuildComponent();

	//implemented by skeleton
	DLAL void dlalDemolishComponent(void* component);
	DLAL void* dlalBuildSystem();
	DLAL void dlalDemolishSystem(void* system);
	DLAL const char* dlalCommandComponent(void* component, const char* command);
	DLAL const char* dlalConnectInput(void* component, void* input);
	DLAL const char* dlalConnectOutput(void* component, void* output);
	DLAL const char* dlalAddComponent(void* system, void* component);
}

namespace dlal{

//returns true if parameter starts with "error"
bool isError(const std::string&);

class Component;

class System{
	public:
		std::string addComponent(Component& component);
		void evaluate(unsigned samples);
	private:
		std::vector<Component*> _components;
};

class Component{
	public:
		Component(): _system(NULL) {}
		virtual ~Component(){}

		//interface for configuration
		//on success, return x such that isError(x) is false
		//on failure, return x such that isError(x) is true
		std::string sendCommand(const std::string&);//see registerCommand
		virtual std::string addInput(Component*){ return "unimplemented"; }
		virtual std::string addOutput(Component*){ return "unimplemented"; }
		virtual std::string readyToEvaluate(){ return "unimplemented"; }

		//evaluation - audio/midi/command processing
		virtual void evaluate(unsigned samples){}

		//interface for evaluation
		virtual float* readAudio(){ return nullptr; }
		virtual MidiMessages* readMidi(){ return nullptr; }
		virtual std::string* readText(){ return nullptr; }

		System* _system;
	protected:
		typedef std::function<std::string(std::stringstream&)> Command;
		void registerCommand(
			const std::string& name,
			const std::string& parameters,
			Command
		);
	private:
		struct CommandWithParameters{
			Command command;
			std::string parameters;
		};
		std::map<std::string, CommandWithParameters> _commands;
};

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
