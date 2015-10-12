#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include "queue.hpp"

#include <dyad.h>

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
	DLAL void dlalDyadInit();
	DLAL void dlalDyadShutdown();
	DLAL void* dlalBuildSystem(int port);
	DLAL char* dlalDemolishSystem(void* system);
	DLAL void dlalSetVariable(void* system, const char* name, const char* value);
	DLAL char* dlalCommand(void* component, const char* command);
	DLAL char* dlalAdd(void* system, void* component, unsigned slot);
	DLAL char* dlalConnect(void* input, void* output);
	DLAL char* dlalDisconnect(void* input, void* output);
}

namespace dlal{

class Component;

//cast to Component
Component* toComponent(void*);

//to uniquely identify component
std::string componentToStr(const Component*);

//allocate c string with contents of c++ string
char* toCStr(const std::string&);

//returns true if parameter starts with "error"
bool isError(const std::string&);

//add audio to components
void add(const float* audio, unsigned size, std::vector<Component*>&);

//add audio to components that have audio
void safeAdd(const float* audio, unsigned size, std::vector<Component*>&);

//pause dyad and do something
std::string dyadPauseAnd(std::function<std::string()>);

class System{
	public:
		enum ReportContext{
			RC_IN_EVALUATION, RC_IN_DYAD, RC_SENTINEL
		};
		System(int port);
		~System();
		std::string add(Component& component, unsigned slot, bool queue=false);
		std::string remove(Component& component, bool queue=false);
		void evaluate();
		std::string set(unsigned sampleRate, unsigned samplesPerEvaluation);
		std::string report(
			ReportContext rc=RC_SENTINEL,
			const std::string& s="",
			const Component* reporter=NULL
		);
		dyad_Stream* dyadNewStream();
		void dyadAddListener(dyad_Stream*, int event, dyad_Callback, void* userData);
		int dyadListenEx(dyad_Stream*, const char* host, int port, int backlog);
		std::vector<dyad_Stream*> _clients;
		std::vector<dyad_Stream*> _streams;
		Queue<std::string> _reportQueue;
		std::vector<std::pair<std::string, std::string>> _reportConnections;
		std::map<std::string, std::string> _variables;
		std::vector<std::vector<Component*>> _components;
	private:
		std::vector<std::vector<Component*>> _componentsToAdd;
		std::vector<Component*> _componentsToRemove;
		std::vector<std::string> _report[RC_SENTINEL];
		std::function<dyad_Stream*()> _dyadNewStream;
		std::function<void(dyad_Stream*, int event, dyad_Callback, void* userData)> _dyadAddListener;
		std::function<int(dyad_Stream*, const char* host, int port, int backlog)> _dyadListenEx;
		dyad_Stream* _server;
};

class Component{
	public:
		Component();
		virtual ~Component(){}
		virtual void* derived(){ return nullptr; }
		virtual std::string type() const=0;

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

		System* _system;
		std::string _label;
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

class SamplesPerEvaluationGetter: public virtual Component{
	public:
		SamplesPerEvaluationGetter();
		virtual ~SamplesPerEvaluationGetter(){}
	protected:
		unsigned _samplesPerEvaluation;
};

class Periodic: public SamplesPerEvaluationGetter{
	public:
		Periodic();
	protected:
		virtual void resize(){}
		virtual void crop(){}
		virtual void reset(){}
		bool phase();
		uint64_t _period, _phase;
	private:
		float _last;
};

class SampleRateGetter: public virtual Component{
	public:
		SampleRateGetter();
		virtual ~SampleRateGetter(){}
	protected:
		unsigned _sampleRate;
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

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
