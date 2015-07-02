#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <map>
#include <sstream>

#ifdef _MSC_VER
	#define DLAL __declspec(dllexport)
	//this is a warning that certain well-defined behavior has occurred
	//there doesn't seem to be a way to silence it in code
	#pragma warning(disable: 4250)
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
	DLAL char* dlalCommand(void* component, const char* command);
	DLAL char* dlalAdd(void* system, void* component, unsigned slot);
	DLAL char* dlalConnect(void* input, void* output);
}

namespace dlal{

typedef void (*TextCallback)(char*);
class Component;

//cast to Component
Component* toComponent(void*);

//allocate c string with contents of c++ string
char* toCStr(const std::string&);

//returns true if parameter starts with "error"
bool isError(const std::string&);

//add audio to components
void add(const float* audio, unsigned size, std::vector<Component*>&);

//add audio to components that have audio
void safeAdd(const float* audio, unsigned size, std::vector<Component*>&);

class System{
	public:
		std::string add(Component& component, unsigned slot, bool queue=false);
		std::string remove(Component& component, bool queue=false);
		void evaluate();
		bool set(std::string variable, unsigned value);
		bool get(std::string variable, unsigned* value=NULL);
		std::string set(unsigned sampleRate, unsigned samplesPerEvaluation);
	private:
		std::map<std::string, std::string> _variables;
		std::vector<std::vector<Component*>> _components;
		std::vector<std::vector<Component*>> _componentsToAdd;
		std::vector<Component*> _componentsToRemove;
};

class Component{
	public:
		Component();
		virtual ~Component(){}
		virtual void* derived(){ return nullptr; }

		//on success, return x such that isError(x) is false
		//on failure, return x such that isError(x) is true
		virtual std::string command(const std::string&);//see registerCommand
		virtual std::string join(System&);//see addJoinAction
		virtual std::string connect(Component& output){ return "error: unimplemented"; }
		virtual std::string disconnect(Component& output){ return "error: unimplemented"; }

		//evaluation - audio/midi/command processing
		virtual void evaluate(){}

		//audio/midi
		virtual void midi(const uint8_t* bytes, unsigned size){}
		virtual bool midiAccepted(){ return false; }
		virtual float* audio(){ return nullptr; }
		virtual bool hasAudio(){ return false; }
	protected:
		typedef std::function<std::string(std::stringstream&)> Command;
		typedef std::function<std::string(System&)> JoinAction;
		void registerCommand(
			const std::string& name,
			const std::string& parameters,
			Command
		);
		void addJoinAction(JoinAction);
	private:
		struct CommandWithParameters{
			Command command;
			std::string parameters;
		};
		std::map<std::string, CommandWithParameters> _commands;
		std::vector<JoinAction> _joinActions;
};

class MultiOut: public virtual Component{
	public:
		MultiOut();
		virtual ~MultiOut(){}
		virtual std::string connect(Component& output);
		virtual std::string disconnect(Component& output);
		bool _checkAudio, _checkMidi;
	protected:
		std::vector<Component*> _outputs;
};

class SamplesPerEvaluationGetter: public virtual Component{
	public:
		SamplesPerEvaluationGetter();
		virtual ~SamplesPerEvaluationGetter(){}
	protected:
		unsigned _samplesPerEvaluation;
};

class SampleRateGetter: public virtual Component{
	public:
		SampleRateGetter();
		virtual ~SampleRateGetter(){}
	protected:
		unsigned _sampleRate;
};

class SystemGetter: public virtual Component{
	public:
		SystemGetter();
		System* _system;
};

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
