#include "commander.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Commander; }

static dlal::Commander* toCommander(void* p){
	return (dlal::Commander*)((dlal::Component*)p)->derived();
}

char* dlalCommanderAdd(
	void* commander, void* component, unsigned slot, unsigned edgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(
		Commander::Directive(*toComponent(component), slot, edgesToWait)
	)) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderConnect(
	void* commander, void* input, void* output, unsigned edgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
		*toComponent(input),
		*toComponent(output),
		edgesToWait
	))) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderSetCallback(void* commander, dlal::TextCallback callback){
	using namespace dlal;
	toCommander(commander)->_callback=callback;
	return toCStr("");
}

namespace dlal{

Commander::Directive::Directive(){}

Commander::Directive::Directive(const std::string& command, unsigned edgesToWait):
	_type(COMMAND), _command(command), _edgesToWait(edgesToWait)
{
	std::stringstream ss(_command);
	ss>>_output;
	ss.ignore(1);
	_command.clear();
	std::getline(ss, _command);
}

Commander::Directive::Directive(
	Component& component, unsigned slot, unsigned edgesToWait
): _type(ADD), _a(&component), _slot(slot), _edgesToWait(edgesToWait) {}

Commander::Directive::Directive(
	Component& input, Component& output, unsigned edgesToWait
): _type(CONNECT), _a(&input), _b(&output), _edgesToWait(edgesToWait) {}

Commander::Commander():
	_queue(8), _callback(nullptr), _size(0), _period(0), _phase(0)
{
	_dequeued.resize(256);
	registerCommand("period", "<period in samples>", [this](std::stringstream& ss){
		ss>>_period;
		return "";
	});
	registerCommand("queue", "<period edges to wait> <output index> command",
		[this](std::stringstream& ss){
			unsigned edgesToWait;
			ss>>edgesToWait;
			std::string s;
			std::getline(ss, s);
			if(!_queue.write(Directive(s, edgesToWait))) return "error: queue full";
			return "";
		}
	);
}

void Commander::evaluate(){
	//dequeue
	while(true){
		if(_dequeued.size()<=_size) _dequeued.resize(_dequeued.size()*2);
		if(!_queue.read(_dequeued[_size], true)) break;
		if(!_dequeued[_size]._edgesToWait) dispatch(_dequeued[_size]);
		else ++_size;
	}
	//update
	_phase+=_samplesPerEvaluation;
	if(_phase<_period) return;
	_phase-=_period;
	//command
	unsigned i=0;
	while(i<_size){
		--_dequeued[i]._edgesToWait;
		if(_dequeued[i]._edgesToWait==0){
			dispatch(_dequeued[i]);
			_dequeued[i]=_dequeued[_size-1];
			--_size;
		}
		else ++i;
	}
}

void Commander::dispatch(const Directive& d){
	std::string result;
	switch(d._type){
		case Directive::COMMAND:
			result=_outputs[d._output]->command(d._command);
			break;
		case Directive::CONNECT:
			result=d._a->connect(*d._b);
			break;
		case Directive::ADD:
			result=_system->add(*d._a, d._slot, true);
			break;
	}
	if(_callback) _callback(dlal::toCStr(result));
}

}//namespace dlal
