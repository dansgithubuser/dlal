#ifndef DLAL_COMMANDER_INCLUDED
#define DLAL_COMMANDER_INCLUDED

#include <skeleton.hpp>

#include <atomic>
#include <vector>

extern "C"{
	DLAL char* dlalCommanderCommand(
		void* commander, void* component, const char* command, unsigned edgesToWait
	);

	DLAL char* dlalCommanderAdd(
		void* commander, void* component, unsigned slot, unsigned edgesToWait
	);

	DLAL char* dlalCommanderConnect(
		void* commander, void* input, void* output, unsigned edgesToWait
	);

	DLAL char* dlalCommanderDisconnect(
		void* commander, void* input, void* output, unsigned edgesToWait
	);

	DLAL char* dlalCommanderRegisterCommand(
		void* commander, const char* name, dlal::TextCallback command
	);
}

namespace dlal{

class Commander: public MultiOut, public Periodic{
	public:
		struct Directive{
			enum Type{ COMMAND, COMMAND_INDEXED, ADD, CONNECT, DISCONNECT };
			Directive();
			Directive(Component&, const std::string& command, unsigned edgesToWait);
			Directive(unsigned i, const std::string& command, unsigned edgesToWait);
			Directive(Component&, unsigned slot, unsigned edgesToWait);
			Directive(Component& input, Component& output, unsigned edgesToWait);
			Directive& disconnect(){ _type=DISCONNECT; return *this; }
			Type _type;
			std::string _command;
			Component* _a;
			Component* _b;
			unsigned _slot, _edgesToWait, _output;
		};
		Commander();
		std::string type() const { return "commander"; }
		void* derived(){ return this; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
		void customCommand(const std::string& name, dlal::TextCallback command);
		Queue<Directive> _queue;
	private:
		void dispatch(const Directive&);
		std::vector<Directive> _dequeued;
		unsigned _size;
};

}//namespace dlal

#endif
