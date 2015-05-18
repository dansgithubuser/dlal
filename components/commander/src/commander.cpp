#include "commander.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Commander; }

namespace dlal{

Commander::Commander(): _queue(8), _size(0), _period(0), _phase(0) {
	_dequeued.resize(256);
	registerCommand("period", "<period in samples>", [&](std::stringstream& ss){
		ss>>_period;
		return "";
	});
	registerCommand("queue", "<period edges to wait> <output index> command", [&](std::stringstream& ss){
		std::string s;
		std::getline(ss, s);
		if(!_queue.write(s)) return "error: queue full";
		return "";
	});
}

std::string Commander::addOutput(Component* output){
	_outputs.push_back(output);
	return "";
}

void Commander::evaluate(unsigned samples){
	//dequeue
	std::string s;
	while(_queue.read(s, true)){
		if(_dequeued.size()<=_size) _dequeued.resize(_dequeued.size()*2);
		_dequeued[_size].fromString(s);
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

Commander::DequeuedCommand::DequeuedCommand(){ _text.resize(256); }

void Commander::DequeuedCommand::fromString(std::string s){
	std::stringstream ss(s);
	ss>>_periodEdgesToWait;
	ss>>_output;
	ss.ignore(1);
	std::getline(ss, _text);
}

void Commander::dispatch(const DequeuedCommand& c){
	_outputs[c._output]->sendCommand(c._text);
}

}//namespace dlal
