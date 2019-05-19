#include "commander.hpp"

#include <cmath>
#include <iostream>

#include <obvious.hpp>

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

std::string Commander::Directive::str() const {
	std::stringstream ss;
	std::string nameA=_nameA, nameB=_nameB;
	if(!nameA.size())
		nameA=_a->_name;
	if(!nameB.size()&&_b)
		nameB=_b->_name;
	ss<<_type<<" "<<nameA<<" ";
	switch(_type){
		case COMMAND: ss<<_command.size()<<" "<<_command; break;
		case CONNECT: ss<<nameB; break;
		case DISCONNECT: ss<<nameB; break;
		default: break;
	}
	return ss.str();
}

void Commander::Directive::dstr(std::stringstream& ss){
	unsigned t;
	ss>>t>>_nameA;
	_type=(Type)t;
	switch(_type){
		case COMMAND:{
			size_t size;
			ss>>size;
			ss.ignore(1);
			_command=read(ss, size);
			break;
		}
		case CONNECT: ss>>_nameB; break;
		case DISCONNECT: ss>>_nameB; break;
	}
}

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
	Component::registerCommand("slots_resize", "size", [this](std::stringstream& ss){
		size_t size;
		ss>>size;
		_slots.resize(size);
		return "";
	});
	Component::registerCommand("slots_list", "size", [this](std::stringstream& ss){
		return ::str(_slots);
	});
	Component::registerCommand("slots_enable", "<enable, default 1>", [this](std::stringstream& ss){
		if(!(ss>>_slotsEnable)) _slotsEnable=1;
		return "";
	});
	Component::registerCommand("slot_clear", "slot", [this](std::stringstream& ss){
		size_t i;
		ss>>i;
		if(i>=_slots.size()) return "error: no such slot";
		_slots[i].clear();
		return "";
	});
	Component::registerCommand("slot_insert", "<before this slot>", [this](std::stringstream& ss){
		size_t i;
		ss>>i;
		if(i>=_slots.size()) return "error: no such slot";
		_slots.insert(_slots.begin()+i, std::vector<Directive>());
		return "";
	});
	Component::registerCommand("slot_command", "slot output command", [this](std::stringstream& ss){
		size_t i;
		void* output;
		ss>>i>>output;
		if(i>=_slots.size()) return "error: no such slot";
		ss.ignore(1);
		std::string s;
		std::getline(ss, s);
		_slots[i].push_back(Directive(*(dlal::Component*)output, s, 0));
		return "";
	});
	Component::registerCommand("slot_connect", "slot input output", [this](std::stringstream& ss){
		size_t i;
		void* input;
		void* output;
		ss>>i>>input>>output;
		if(i>=_slots.size()) return "error: no such slot";
		_slots[i].push_back(Directive(*(dlal::Component*)input, *(dlal::Component*)output, 0));
		return "";
	});
	Component::registerCommand("slot_disconnect", "slot input output", [this](std::stringstream& ss){
		size_t i;
		void* input;
		void* output;
		ss>>i>>input>>output;
		if(i>=_slots.size()) return "error: no such slot";
		_slots[i].push_back(Directive(*(dlal::Component*)input, *(dlal::Component*)output, 0).disconnect());
		return "";
	});
	Component::registerCommand("slot_skip_to", "slot", [this](std::stringstream& ss){
		size_t i;
		ss>>i;
		if(i>=_slots.size()) return "error: no such slot";
		while(_slot!=i){
			for(auto i: _slots[_slot]) dispatch(i);
			++_slot;
			_slot%=_slots.size();
		}
		return "";
	});
	registerCommand("serialize_commander", "", [this](std::stringstream&){
		return ::str(_slots);
	});
	registerCommand("deserialize_commander", "<serialized>", [this](std::stringstream& ss){
		::dstr(ss, _slots);
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
	//slots
	if(_slots.size()&&_slotsEnable){
		for(auto i: _slots[_slot]) dispatch(i);
		++_slot;
		_slot%=_slots.size();
	}
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

void Commander::dispatch(Directive& d){
	std::string result;
	if(!d._a)
		d._a=_system->_nameToComponent.at(d._nameA);
	if(!d._b&&d._nameB.size())
		d._b=_system->_nameToComponent.at(d._nameB);
	switch(d._type){
		case Directive::COMMAND:
			result=d._a->command(d._command);
			_system->_reports.write((std::string)"command "+_name+" "+d._a->_name);
			break;
		case Directive::COMMAND_INDEXED:
			result=_outputs[d._output]->command(d._command);
			break;
		case Directive::ADD:
			result=_system->add(*d._a, d._slot);
			break;
		case Directive::CONNECT:
			result=_system->connect(*d._a, *d._b);
			break;
		case Directive::DISCONNECT:
			result=_system->connect(*d._a, *d._b, false);
			break;
	}
	if(result.size()) _system->_reports.write(result);
}

}//namespace dlal
