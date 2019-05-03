#include "commander.hpp"

#include <cmath>
#include <iostream>

DLAL_BUILD_COMPONENT_DEFINITION(Commander)

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
	_queue(8), _nDequeued(0)
{
	_dequeued.resize(256);
	registerCommand("queue_indexed", "<period edges to wait> <output index> command",
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
	registerCommand("queue", "<period edges to wait> <output> command",
		[this](std::stringstream& ss){
			unsigned edgesToWait;
			void* output;
			ss>>edgesToWait>>output;
			ss.ignore(1);
			std::string s;
			std::getline(ss, s);
			if(!_queue.write(Directive(*(dlal::Component*)output, s, edgesToWait)))
				return "error: queue full";
			return "";
		}
	);
	Component::registerCommand("queue_resize", "size", [this](std::stringstream& ss){
		unsigned size;
		ss>>size;
		_queue.resize(unsigned(std::log2(size))+1);
		return "";
	});
	Component::registerCommand("lockless", "", [this](std::stringstream& ss){
		return _queue.lockless()?"lockless":"lockfull";
	});
}

void Commander::evaluate(){
	//dequeue
	while(true){
		if(_dequeued.size()<=_nDequeued) _dequeued.resize(_dequeued.size()*2);
		if(!_queue.read(_dequeued[_nDequeued], true)) break;
		if(!_dequeued[_nDequeued]._edgesToWait) dispatch(_dequeued[_nDequeued]);
		else ++_nDequeued;
	}
	//update
	if(!phase()) return;
	//command
	unsigned i=0;
	while(i<_nDequeued){
		--_dequeued[i]._edgesToWait;
		if(_dequeued[i]._edgesToWait==0){
			dispatch(_dequeued[i]);
			_dequeued[i]=_dequeued[_nDequeued-1];
			--_nDequeued;
		}
		else ++i;
	}
}

void Commander::midi(const uint8_t* bytes, unsigned size){
	std::stringstream ss;
	ss<<"midi ";
	for(unsigned i=0; i<size; ++i) ss<<(unsigned)bytes[i]<<" ";
	_queue.write(Directive(0, ss.str(), 0));
}

void Commander::dispatch(const Directive& d){
	std::string result;
	switch(d._type){
		case Directive::COMMAND:
			result=d._a->command(d._command);
			_system->_reports.write((std::string)"command "+componentToStr(this)+" "+componentToStr(d._a));
			break;
		case Directive::COMMAND_INDEXED:
			result=_outputs[d._output]->command(d._command);
			break;
		case Directive::ADD:
			result=_system->add(*d._a, d._slot);
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
