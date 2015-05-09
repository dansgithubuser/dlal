#include "commander.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Commander; }

namespace dlal{

Commander::Commander(): _queue(8), _period(0), _phase(0) {
	registerCommand("period", "<period in samples>", [&](std::stringstream& ss){
		ss>>_period;
		return "";
	});
	registerCommand("queue", "<output index> command", [&](std::stringstream& ss){
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

std::string Commander::readyToEvaluate(){
	if(!_period) return "error: period must be set";
	return "";
}

void Commander::evaluate(unsigned samples){
	_phase+=samples;
	if(_phase<_period) return;
	_phase-=_period;
	std::string s;
	while(_queue.read(s, true)){
		std::stringstream ss(s);
		unsigned i;
		ss>>i;
		if(i>=_outputs.size()) continue;
		std::getline(ss, s);
		_outputs[i]->sendCommand(s);
	}
}

}//namespace dlal
