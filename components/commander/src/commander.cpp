#include "commander.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Commander; }

static dlal::Commander* toCommander(void* p){ return (dlal::Commander*)p; }

char* dlalCommanderConnectInput(
	void* commander, void* component, void* input, unsigned periodEdgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
			toComponent(component),
			toComponent(input),
			Commander::Directive::CONNECT_INPUT,
			periodEdgesToWait
	))) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderConnectOutput(
	void* commander, void* component, void* output, unsigned periodEdgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
		toComponent(component),
		toComponent(output),
		Commander::Directive::CONNECT_OUTPUT,
		periodEdgesToWait
	))) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderAddComponent(
	void* commander, void* component, unsigned periodEdgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(
		Commander::Directive(toComponent(component), periodEdgesToWait)
	)) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderSetCallback(void* commander, dlal::TextCallback callback){
	using namespace dlal;
	toCommander(commander)->_callback=callback;
	return toCStr("");
}

namespace dlal{

Commander::Directive::Directive(){}

Commander::Directive::Directive(const std::string& command):
	_type(COMMAND), _command(command)
{
	std::stringstream ss(_command);
	ss>>_periodEdgesToWait;
	ss>>_output;
	ss.ignore(1);
	_command.clear();
	std::getline(ss, _command);
}

Commander::Directive::Directive(
	Component* a, Component* b, Type t, unsigned periodEdgesToWait
): _type(t), _a(a), _b(b), _periodEdgesToWait(periodEdgesToWait) {}

Commander::Directive::Directive(
	Component* component, unsigned periodEdgesToWait
): _type(ADD), _a(component), _periodEdgesToWait(periodEdgesToWait) {}

Commander::Commander():
	_queue(8), _callback(NULL), _size(0), _period(0), _phase(0)
{
	_dequeued.resize(256);
	registerCommand("period", "<period in samples>", [&](std::stringstream& ss){
		ss>>_period;
		return "";
	});
	registerCommand("queue", "<period edges to wait> <output index> command",
		[&](std::stringstream& ss){
			std::string s;
			std::getline(ss, s);
			if(!_queue.write(Directive(s))) return "error: queue full";
			return "";
		}
	);
}

std::string Commander::addOutput(Component* output){
	_outputs.push_back(output);
	return "";
}

void Commander::evaluate(unsigned samples){
	//dequeue
	while(true){
		if(_dequeued.size()<=_size) _dequeued.resize(_dequeued.size()*2);
		if(!_queue.read(_dequeued[_size], true)) break;
		if(!_dequeued[_size]._periodEdgesToWait) dispatch(_dequeued[_size]);
		else ++_size;
	}
	//update
	_phase+=samples;
	if(_phase<_period) return;
	_phase-=_period;
	//command
	unsigned i=0;
	while(i<_size){
		--_dequeued[i]._periodEdgesToWait;
		if(_dequeued[i]._periodEdgesToWait==0){
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
			result=_outputs[d._output]->sendCommand(d._command);
			break;
		case Directive::CONNECT_INPUT:
			result=d._a->addInput(d._b);
			break;
		case Directive::CONNECT_OUTPUT:
			result=d._a->addOutput(d._b);
			break;
		case Directive::ADD:
			result=_system->queueAddComponent(*d._a);
			break;
	}
	if(_callback) _callback(dlal::toCStr(result));
}

}//namespace dlal
