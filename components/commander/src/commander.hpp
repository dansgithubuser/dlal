#ifndef DLAL_COMMANDER_INCLUDED
#define DLAL_COMMANDER_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <atomic>
#include <vector>

extern "C"{
	DLAL char* dlalCommanderAdd(
		void* commander, void* component, unsigned slot, unsigned edgesToWait
	);

	DLAL char* dlalCommanderConnect(
		void* commander, void* input, void* output, unsigned edgesToWait
	);

	DLAL char* dlalCommanderSetCallback(
		void* commander, dlal::TextCallback callback
	);
}

namespace dlal{

class Commander:
	public MultiOut, public SamplesPerEvaluationGetter, public SystemGetter
{
	public:
		struct Directive{
			enum Type{ COMMAND, ADD, CONNECT };
			Directive();
			Directive(const std::string& command, unsigned edgesToWait);
			Directive(Component&, unsigned slot, unsigned edgesToWait);
			Directive(Component& input, Component& output, unsigned edgesToWait);
			Type _type;
			std::string _command;
			Component* _a;
			Component* _b;
			unsigned _slot, _edgesToWait, _output;
		};
		Commander();
		void* derived(){ return this; }
		void evaluate();
		Queue<Directive> _queue;
		TextCallback _callback;
	private:
		void dispatch(const Directive&);
		std::vector<Directive> _dequeued;
		unsigned _size;
		unsigned _period, _phase;
};

}//namespace dlal

#endif
