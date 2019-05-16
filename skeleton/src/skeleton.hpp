#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include "queue.hpp"

#include <atomic>
#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <map>
#include <mutex>
#include <sstream>

#ifdef _MSC_VER
	#define DLAL __declspec(dllexport)
	//this is a warning that certain well-defined behavior has occurred
	//there doesn't seem to be a way to silence it in code
	#pragma warning(disable: 4250)
#else
	#define DLAL
#endif

#define DLAL_BUILD_COMPONENT_DEFINITION(COMPONENT)\
	extern "C" {\
		DLAL const char* dlalBuildComponent(const char* name){\
			auto component=new dlal::COMPONENT;\
			component->_name=name;\
			std::stringstream ss;\
			ss<<(void*)(dlal::Component*)component;\
			static std::string s;\
			s=ss.str();\
			return s.c_str();\
		}\
	}

namespace dlal{

class Component;

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
		System();
		std::string add(Component& component, unsigned slot);
		std::string remove(Component& component);
		std::string check();
		void evaluate();
		std::string set(unsigned sampleRate, unsigned samplesPerEvaluation);
		std::string setVariable(std::string name, std::string value);
		std::string rename(Component& component, std::string newName);
		std::string handleRequest(std::string request);

		Queue<std::string> _reports;//populated in evaluation
		std::vector<std::pair<std::string, std::string>> _connections;
		std::map<std::string, std::string> _variables;
		std::vector<std::vector<Component*>> _components;
		std::map<std::string, Component*> _nameToComponent;
		Queue<std::string> _requests;//read in evaluation
};

class Component{
	public:
		Component();
		virtual ~Component(){}
		virtual void* derived(){ return nullptr; }
		virtual std::string type() const=0;
		std::string str() const;

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
		void midiSend(Component* target, const uint8_t* bytes, unsigned size) const;
		virtual float* audio(){ return nullptr; }
		virtual bool hasAudio(){ return false; }

		System* _system;
		std::string _name;
	protected:
		typedef std::function<std::string(std::stringstream&)> Command;
		typedef std::function<std::string(System&)> JoinAction;
		void registerCommand(
			const std::string& name,
			const std::string& parameters,
			Command
		);
		std::string command(std::stringstream&);
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
		virtual ~Periodic(){}
	protected:
		virtual std::string resize(uint64_t period);
		virtual std::string setPhase(uint64_t phase);
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
		virtual std::string connect(Component& output) override;
		virtual std::string disconnect(Component& output) override;
		bool _checkAudio, _checkMidi;
	protected:
		std::vector<Component*> _outputs;
		int _maxOutputs=0;
};

class MidiControllee: public virtual Component{
	public:
		MidiControllee();
		virtual void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
	protected:
		std::map<std::string, float*> _nameToControl;
	private:
		enum class PretendControl{
			PITCH_WHEEL=0x100,
			SENTINEL
		};
		class Range{
			public:
				Range(): _new(true) {}
				operator int(){ return _max-_min; }
				void value(int v);
				int _min, _max;
			private:
				bool _new;
		};
		struct Control{
			Control(): _control(NULL) { _f.push_back(0.0f); _f.push_back(1.0f); }
			int _min, _max;
			std::vector<float> _f;
			float* _control;
		};
		float* _listening;
		std::map<int, Range> _listeningControls;
		std::vector<Control> _controls;
};

class Dummy: public SamplesPerEvaluationGetter{
	public:
		Dummy(){ addJoinAction([this](System&){ _audio.resize(_samplesPerEvaluation, .101f); return ""; }); }
		std::string type() const override { return "dummy"; }
		float* audio() override { return _audio.data(); }
		bool hasAudio() override { return true; }
		std::vector<float> _audio;
};

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
