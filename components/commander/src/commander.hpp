#ifndef DLAL_COMMANDER_INCLUDED
#define DLAL_COMMANDER_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <atomic>
#include <vector>

extern "C"{
	DLAL char* dlalCommanderConnectInput(void* commander, void* component, void* input, unsigned periodEdgesToWait);
	DLAL char* dlalCommanderConnectOutput(void* commander, void* component, void* output, unsigned periodEdgesToWait);
	DLAL char* dlalCommanderAddComponent(void* commander, void* component, unsigned periodEdgesToWait);
	DLAL char* dlalCommanderSetCallback(void* commander, dlal::TextCallback callback);
}

namespace dlal{

class Commander: public Component{
	public:
		struct Directive{
			enum Type{ COMMAND, CONNECT_INPUT, CONNECT_OUTPUT, ADD };
			Directive();
			Directive(const std::string& command);
			Directive(Component* a, Component* b, Type, unsigned periodEdgesToWait);
			Directive(Component*, unsigned periodEdgesToWait);
			Type _type;
			std::string _command;
			Component* _a;
			Component* _b;
			unsigned _periodEdgesToWait;
			unsigned _output;
		};
		Commander();
		std::string addOutput(Component*);
		void evaluate(unsigned samples);
		Queue<Directive> _queue;
		TextCallback _callback;
	private:
		void dispatch(const Directive&);
		std::vector<Directive> _dequeued;
		unsigned _size;
		std::vector<Component*> _outputs;
		unsigned _period, _phase;
};

}//namespace dlal

#endif
