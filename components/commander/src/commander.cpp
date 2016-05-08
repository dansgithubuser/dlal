#include "commander.hpp"

#include <cmath>
#include <iostream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Commander; }

static dlal::Commander* toCommander(void* p){
	return (dlal::Commander*)((dlal::Component*)p)->derived();
}

char* dlalCommanderCommand(
	void* commander, void* component, const char* command, unsigned edgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
			*toComponent(component), std::string(command), edgesToWait
	))) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderAdd(
	void* commander, void* component, unsigned slot, unsigned edgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
		*toComponent(component), slot, edgesToWait
	))) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderConnect(
	void* commander, void* input, void* output, unsigned edgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
		*toComponent(input), *toComponent(output), edgesToWait
	))) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderDisconnect(
	void* commander, void* input, void* output, unsigned edgesToWait
){
	using namespace dlal;
	if(!toCommander(commander)->_queue.write(Commander::Directive(
		*toComponent(input), *toComponent(output), edgesToWait
	).disconnect())) return toCStr("error: queue full");
	return toCStr("");
}

char* dlalCommanderRegisterCommand(
	void* commander, const char* name, dlal::TextCallback command
){
	using namespace dlal;
	toCommander(commander)->customCommand(std::string(name), command);
	return toCStr("");
}

namespace dlal{

Commander::Directive::Directive(){}

Commander::Directive::Directive(
	Component& component, const std::string& command, unsigned edgesToWait
):
	_type(COMMAND), _command(command), _a(&component), _edgesToWait(edgesToWait)
{}

Commander::Directive::Directive(
	unsigned i, const std::string& command, unsigned edgesToWait
):
	_type(COMMAND_INDEXED),
	_command(command),
	_edgesToWait(edgesToWait),
	_output(i)
{}

Commander::Directive::Directive(
	Component& component, unsigned slot, unsigned edgesToWait
): _type(ADD), _a(&component), _slot(slot), _edgesToWait(edgesToWait) {}

Commander::Directive::Directive(
	Component& input, Component& output, unsigned edgesToWait
): _type(CONNECT), _a(&input), _b(&output), _edgesToWait(edgesToWait) {}

Commander::Commander():
	_queue(8), _size(0)
{
	_dequeued.resize(256);
	registerCommand("queue", "<period edges to wait> <output index> command",
		[this](std::stringstream& ss){
			unsigned edgesToWait, output;
			ss>>edgesToWait>>output;
			ss.ignore(1);
			std::string s;
			std::getline(ss, s);
			if(!_queue.write(Directive(output, s, edgesToWait)))
				return "error: queue full";
			return "";
		}
	);
	registerCommand("queue_resize", "size", [this](std::stringstream& ss){
		unsigned size;
		ss>>size;
		_queue.resize(unsigned(std::log2(size))+1);
		return "";
	});
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return _queue.lockless()?"lockless":"lockfull";
	});
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
	if(!phase()) return;
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

void Commander::customCommand(
	const std::string& name, dlal::TextCallback command
){
	registerCommand(name, "", [this, command](std::stringstream& ss){
		command(dlal::toCStr(ss.str()));
		return "";
	});
}

void Commander::dispatch(const Directive& d){
	std::string result;
	switch(d._type){
		case Directive::COMMAND:
			result=d._a->command(d._command);
			_system->_reportQueue.write((std::string)"command "+componentToStr(this)+" "+componentToStr(d._a));
			break;
		case Directive::COMMAND_INDEXED:
			result=_outputs[d._output]->command(d._command);
			break;
		case Directive::ADD:
			result=_system->add(*d._a, d._slot, true);
			break;
		case Directive::CONNECT:
			result=d._a->connect(*d._b);
			break;
		case Directive::DISCONNECT:
			result=d._a->disconnect(*d._b);
			break;
	}
	if(result.size()) std::cerr<<result<<std::endl;
}

}//namespace dlal
