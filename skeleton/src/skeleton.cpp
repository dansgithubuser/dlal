#include "skeleton.hpp"

#include <obvious.hpp>

#include <algorithm>
#include <cstring>
#include <cstdlib>
#include <iostream>
#include <set>
#include <stdexcept>
#include <thread>

static std::istream& operator>>(std::istream& istream, dlal::Component*& component){
	void* v;
	istream>>v;
	component=(dlal::Component*)v;
	return istream;
}

extern "C" {

DLAL const char* dlalRequest(const char* request, bool immediate){
	#if 0
		std::cout<<immediate<<" "<<request<<"\n";
	#endif
	static std::set<dlal::System*> systems;
	static dlal::System* active=nullptr;
	static std::string s;
	if(immediate){
		std::stringstream ss(request);
		ss>>s;
		//systems and memory management
		if(s=="system/build"){
			auto system=new dlal::System;
			systems.insert(system);
			s=str((void*)system);
		}
		else if(s=="system/switch"){
			s=str((void*)active);
			void* system;
			ss>>system;
			active=(dlal::System*)system;
		}
		else if(s=="system/demolish"){
			void* system;
			ss>>system;
			if(system==active) active=nullptr;
			delete (dlal::System*)system;
			systems.erase((dlal::System*)system);
			s="";
		}
		else if(s=="component/demolish"){
			dlal::Component* c;
			ss>>c;
			delete c;
		}
		else if(!active){
			//systemless component commands
			if(s=="component/connect"){
				dlal::Component* a;
				dlal::Component* b;
				ss>>a>>b;
				s=a->connect(*b);
			}
			else if(s=="component/disconnect"){
				dlal::Component* a;
				dlal::Component* b;
				ss>>a>>b;
				s=a->disconnect(*b);
			}
			else if(s=="component/command"){
				dlal::Component* c;
				ss>>c;
				std::getline(ss, s);
				s=c->command(s);
			}
			else return "error: no active system\n";
		}
		else s=active->handleRequest(request);
		return s.c_str();
	}
	else if(!active) return "error: no active system\n";
	else{
		static int requestNumber=0;
		++requestNumber;
		active->_requests.write(std::to_string(requestNumber)+" "+request);
		s=std::to_string(requestNumber);
		return s.c_str();
	}
}

}//extern "C"

namespace dlal{

bool isError(const std::string& s){ return s.compare(0, 5, "error")==0; }

void add(
	const float* audio, unsigned size, std::vector<Component*>& components
){
	for(auto i: components)
		for(unsigned j=0; j<size; ++j) i->audio()[j]+=audio[j];
}

void safeAdd(
	const float* audio, unsigned size, std::vector<Component*>& components
){
	for(auto i: components) if(i->hasAudio())
			for(unsigned j=0; j<size; ++j) i->audio()[j]+=audio[j];
}

//=====System=====//
System::System():
	_reports(8),
	_requests(8)
{}

std::string System::add(Component& component, unsigned slot){
	for(auto i: _components) for(auto j: i) if(j==&component) return "error: already added";
	std::string r=component.join(*this);
	if(isError(r)) return r;
	if(_components.size()<=slot) _components.resize(slot+1);
	_components[slot].push_back(&component);
	_nameToComponent[component._name]=&component;
	_reports.write("add "+component._name+" "+component.type());
	return "";
}

std::string System::remove(Component& component){
	unsigned slot;
	std::vector<Component*>::iterator it;
	if(!findComponent(component, slot, it)) return "error: component was not added";
	_components[slot].erase(it);
	_reports.write("remove "+component._name);
	return "";
}

std::string System::reslot(Component& component, unsigned newSlot){
	unsigned slot;
	std::vector<Component*>::iterator it;
	if(!findComponent(component, slot, it)) return "error: component was not added";
	_components[slot].erase(it);
	if(_components.size()<=newSlot) _components.resize(newSlot+1);
	_components[newSlot].push_back(&component);
	_reports.write(::str("reslot", component._name, slot));
	return "";
}

std::string System::swap(Component& a, Component& b){
	unsigned aSlot, bSlot;
	std::vector<Component*>::iterator aIt, bIt;
	if(!findComponent(a, aSlot, aIt)) return "error: component a was not added";
	if(!findComponent(b, bSlot, bIt)) return "error: component b was not added";
	*aIt=&b;
	*bIt=&a;
	auto aConnectors=OBV_FOR(
		_connections,
		if(i->second==a._name) r.push_back(i->first),
		std::vector<std::string>()
	);
	auto bConnectors=OBV_FOR(
		_connections,
		if(i->second==b._name) r.push_back(i->first),
		std::vector<std::string>()
	);
	for(auto i: aConnectors){
		Component& c=*_nameToComponent.at(i);
		connect(c, a, "disable");
		connect(c, b, "enable");
	}
	for(auto i: bConnectors){
		Component& c=*_nameToComponent.at(i);
		connect(c, b, "disable");
		connect(c, a, "enable");
	}
	_reports.write(::str("swap", a._name, b._name));
	return "";
}

std::string System::connect(Component& a, Component& b, std::string action){
	const auto pair=std::pair<std::string, std::string>(a._name, b._name);
	bool enable;
	//decide if it's a connect or a disconnect
	if(action=="enable") enable=true;
	else if(action=="disable") enable=false;
	else if(action=="toggle") enable=!in(pair, _connections);
	else return "error: invalid connect action";
	//act
	std::string s=enable?a.connect(b):a.disconnect(b);
	//bookkeeping
	if(!isError(s)){
		_reports.write((enable?"connect ":"disconnect ")+a._name+" "+b._name);
		if(enable) _connections.push_back(pair);
		else for(unsigned i=0; i<_connections.size(); ++i)
			if(_connections[i]==pair){
				_connections[i]=_connections.back();
				_connections.pop_back();
				break;
			}
	}
	//
	return s;
}

std::string System::prep(){
	std::set<std::string> components;
	for(auto connection: _connections){
		components.insert(connection.first);
		components.insert(connection.second);
	}
	for(auto slot: _components)
		for(auto component: slot)
			components.erase(component->_name);
	if(components.size()) return "error: connected components have not been added";
	for(auto slot: _components)
		for(auto component: slot){
			std::string s=component->prep();
			if(isError(s)) return s;
		}
	return "";
}

void System::evaluate(){
	static std::string s, requestNumber;
	while(_requests.read(s, true)){
		std::stringstream ss(s);
		ss>>requestNumber;
		std::getline(ss, s);
		s=handleRequest(s);
		_reports.write(requestNumber+": "+s);
	}
	for(auto i: _components)
		for(auto j: i){
			#if 0
				std::cout<<"evaluate "<<j->_name<<"\n";
			#endif
			j->evaluate();
		}
}

std::string System::set(unsigned sampleRate, unsigned log2SamplesPerEvaluation){
	if(!sampleRate||!log2SamplesPerEvaluation)
		return "error: must set sample rate and log2 samples per evaluation";
	_variables["sampleRate"]=std::to_string(sampleRate);
	_variables["samplesPerEvaluation"]=std::to_string(1<<log2SamplesPerEvaluation);
	return "";
}

std::string System::setVariable(std::string name, std::string value){
	if(std::string(name ).find('\n')!=std::string::npos)
		return "error: name cannot contain newline";
	if(std::string(value).find('\n')!=std::string::npos)
		return "error: value cannot contain newline";
	_variables[name]=value;
	_reports.write("variable "+name+"\n"+value+"\n");
	return "";
}

std::string System::rename(Component& component, std::string newName){
	std::string oldName=component._name;
	for(auto& i: _connections){
		if(i.first==oldName) i.first=newName;
		if(i.second==oldName) i.second=newName;
	}
	component._name=newName;
	_nameToComponent[newName]=&component;
	_nameToComponent.erase(oldName);
	_reports.write(str("rename", oldName, newName));
	return "";
}

std::string System::handleRequest(std::string request){
	std::stringstream ss(request);
	std::string command;
	ss>>command;
	std::string s;
	if(command=="system/report"){
		if(_reports.read(s, true)) return s;
	}
	else if(command=="system/prep"){
		return prep();
	}
	else if(command=="system/evaluate"){
		evaluate();
	}
	else if(command=="variable/get"){
		if(ss>>s){
			if(!_variables.count(s)) return "error: no such variable";
			return _variables.at(s);
		}
		else{
			std::stringstream ss;
			ss<<str(_variables);
			return ss.str();
		}
	}
	else if(command=="variable/set"){
		std::string name, value;
		ss>>std::ws;
		std::getline(ss, name);
		std::getline(ss, value);
		return setVariable(name, value);
	}
	else if(command=="variable/unset"){
		ss>>s;
		if(!_variables.count(s)) return "error: no such variable";
		_variables.erase(s);
	}
	else if(command=="component/get"){
		if(ss>>s){
			if(!_nameToComponent.count(s)) return str("error: no such component", s);
			return str((void*)_nameToComponent.at(s));
		}
		else{
			std::stringstream ss;
			ss<<str(_components);
			return ss.str();
		}
	}
	else if(command=="component/get/connections"){
		std::stringstream ss;
		ss<<str(_connections);
		return ss.str();
	}
	else if(command=="component/name"){
		Component* c;
		ss>>c;
		ss>>c->_name;
	}
	else if(command=="component/add"){
		Component* c;
		ss>>c;
		unsigned slot;
		ss>>slot;
		return add(*c, slot);
	}
	else if(command=="component/remove"){
		Component* c;
		ss>>c;
		return remove(*c);
	}
	else if(command=="component/reslot"){
		Component* c;
		size_t slot;
		ss>>c>>slot;
		return reslot(*c, slot);
	}
	else if(command=="component/swap"){
		Component* a;
		Component* b;
		ss>>a>>b;
		return swap(*a, *b);
	}
	else if(command=="component/rename"){
		Component* c;
		ss>>c>>s;
		return rename(*c, s);
	}
	else if(command=="component/connect"){
		Component* a;
		Component* b;
		ss>>a>>b;
		return connect(*a, *b);
	}
	else if(command=="component/disconnect"){
		Component* a;
		Component* b;
		ss>>a>>b;
		return connect(*a, *b, "disable");
	}
	else if(command=="component/connect/toggle"){
		Component* a;
		Component* b;
		ss>>a>>b;
		return connect(*a, *b, "toggle");
	}
	else if(command=="component/command"){
		Component* c;
		ss>>c;
		std::getline(ss, s);
		return c->command(s);
	}
	else return ::str("error: no such command", command);
	return "";
}

bool System::findComponent(
	const Component& component,
	unsigned& slot,
	std::vector<Component*>::iterator& it
){
	for(slot=0; slot<_components.size(); ++slot){
		auto& s=_components[slot];
		it=std::find(s.begin(), s.end(), &component);
		if(it!=_components[slot].end()) return true;
	}
	return false;
}
//=====Component=====//
Component::Component(): _system(nullptr) {
	addJoinAction([this](System& system){
		_system=&system;
		return "";
	});
	registerCommand("help", "", [this](std::stringstream& ss){
		std::string result="recognized commands are:\n";
		for(auto i: _commands) result+=i.first+" "+i.second.parameters+"\n";
		return result;
	});
	registerCommand("type", "", [this](std::stringstream&){
		return type();
	});
	registerCommand("name", "", [this](std::stringstream&){
		return _name;
	});
	registerCommand("midi", "byte[1]..byte[n]", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		unsigned byte;
		while(ss>>byte) bytes.push_back(byte);
		midi(bytes.data(), bytes.size());
		return "";
	});
	registerCommand("serialize", "", [this](std::stringstream&){
		std::stringstream ss;
		for(auto i: _commands) if(startsWith(i.first, "serialize_")){
			std::stringstream ss2;
			ss<<i.second.command(ss2)<<" ";
		}
		return ss.str();
	});
	registerCommand("deserialize", "<serialized>", [this](std::stringstream& ss){
		for(auto i: _commands) if(startsWith(i.first, "deserialize_")){
			#if 0
				std::cout<<_name<<" "<<i.first<<"\n";
			#endif
			i.second.command(ss);
		}
		return "";
	});
}

std::string Component::str() const {
	return ::str(_name);
}

std::string Component::command(const std::string& s){
	std::stringstream ss(s);
	return command(ss);
}

std::string Component::join(System& system){
	for(auto i: _joinActions){
		auto r=i(system);
		if(isError(r)) return r;
	}
	return "";
}

void Component::midiSend(Component* target, const uint8_t* bytes, unsigned size) const {
	target->midi(bytes, size);
	_system->_reports.write((std::string)"midi "+_name+" "+target->_name);
}

void Component::registerCommand(
	const std::string& name,
	const std::string& parameters,
	Command command
){
	_commands[name]={command, parameters};
}

std::string Component::command(std::stringstream& ss){
	std::string s;
	ss>>s;
	if(!_commands.count(s))
		return "error: "+s+" unrecognized\n"+_commands["help"].command(ss);
	ss.get();
	return _commands[s].command(ss);
}

void Component::addJoinAction(JoinAction j){ _joinActions.push_back(j); }

//=====SamplesPerEvaluationGetter=====//
SamplesPerEvaluationGetter::SamplesPerEvaluationGetter(): _samplesPerEvaluation(0) {
	registerCommand("set_samples_per_evaluation", "<sample per evaluation>", [this](std::stringstream& ss){
		if(ss>>_samplesPerEvaluation) return "";
		return "error: couldn't read samples per evaluation";
	});
	addJoinAction([this](System& system){
		if(!system._variables.count("samplesPerEvaluation"))
			return "error: system does not have samplesPerEvaluation";
		_samplesPerEvaluation=std::stoi(system._variables["samplesPerEvaluation"]);
		return "";
	});
}

//=====Periodic=====//
Periodic::Periodic(): _period(0), _phase(0), _last(0.0f) {
	registerCommand("periodic", "", [this](std::stringstream& ss){
		std::stringstream tt;
		tt<<(void*)(Periodic*)this;
		return tt.str();
	});
	registerCommand("periodic_resize", "<period in samples>", [this](std::stringstream& ss){
		uint64_t period;
		ss>>period;
		return resize(period);
	});
	registerCommand("periodic_crop", "", [this](std::stringstream& ss){
		auto s=resize(_phase);
		if(isError(s)) return s;
		return setPhase(0);
	});
	registerCommand("periodic_get", "", [this](std::stringstream& ss){
		std::string result=std::to_string(_period)+" "+std::to_string(_phase);
		return result;
	});
	registerCommand("periodic_set_phase", "<phase>", [this](std::stringstream& ss){
		uint64_t phase;
		ss>>phase;
		auto s=setPhase(phase);
		return s;
	});
	registerCommand("periodic_match", "<other periodic>", [this](std::stringstream& ss){
		void* v;
		ss>>v;
		auto other=(Periodic*)v;
		auto s=resize(other->_period);
		if(isError(s)) return s;
		s=setPhase(other->_phase);
		return s;
	});
	registerCommand("serialize_periodic", "", [this](std::stringstream& ss){
		return std::to_string(_period);
	});
	registerCommand("deserialize_periodic", "<serialized>", [this](std::stringstream& ss){
		ss>>_period;
		return "";
	});
}

std::string Periodic::resize(uint64_t period){
	_period=period;
	if(_period) _phase%=_period;
	else _phase=0;
	return "";
}

std::string Periodic::setPhase(uint64_t phase){
	_phase=phase;
	_last=0.0f;
	return "";
}

bool Periodic::phase(){
	_phase+=_samplesPerEvaluation;
	if(_phase<_period){
		float current=1.0f*_phase/_period;
		if(current-_last>0.01f){
			_system->_reports.write((std::string)"phase "+_name+" "+std::to_string(current));
			_last=current;
		}
		return false;
	}
	_phase-=_period;
	_system->_reports.write((std::string)"edge "+_name);
	_last=0.0f;
	return true;
}

//=====SampleRateGetter=====//
SampleRateGetter::SampleRateGetter(): _sampleRate(0) {
	registerCommand("set_sample_rate", "<sample rate>", [this](std::stringstream& ss){
		if(ss>>_sampleRate) return "";
		return "error: couldn't read sample rate";
	});
	addJoinAction([this](System& system){
		if(!system._variables.count("sampleRate"))
			return "error: system does not have sampleRate";
		_sampleRate=std::stoi(system._variables["sampleRate"]);
		return "";
	});
}

//=====MultiOut=====//
MultiOut::MultiOut(): _checkAudio(false), _checkMidi(false) {
	addJoinAction([this](System& system){
		std::stringstream ss;
		for(auto i: _outputs)
			ss<<"connect "+_name+" "+i->_name<<" ";
		if(ss.str().size()) system._reports.write(ss.str());
		return "";
	});
}

std::string MultiOut::connect(Component& output){
	if(_checkAudio&&!output.hasAudio())
		return "error: output must have audio";
	if(_checkMidi&&!output.midiAccepted())
		return "error: output must accept midi";
	if(std::find(_outputs.begin(), _outputs.end(), &output)!=_outputs.end())
		return "warning: output already connected";
	if(_maxOutputs&&_outputs.size()==_maxOutputs)
		return "error: max outputs already connected";
	_outputs.push_back(&output);
	return "";
}

std::string MultiOut::disconnect(Component& output){
	auto i=std::find(_outputs.begin(), _outputs.end(), &output);
	if(i==_outputs.end()) return "warning: component was not connected";
	_outputs.erase(i);
	return "";
}

//=====MidiControllee=====//
MidiControllee::MidiControllee(){
	registerCommand("control_set", "control number [min value] [max value]", [this](std::stringstream& ss){
		if(peek(ss, 1)=="?") return
			"Map MIDI controller with specified number to control with specified name.\n"
			"To get a list of control names, use control_list.\n"
			"If the controller doesn't have a full range from 0 to 127, its range can be specified.";
		std::string control;
		int number, min=0, max=127;
		ss>>control>>number>>min>>max;
		if(!_nameToControl.count(control)) return "error: unknown control";
		if(number>127) return "error: controller number too high";
		addControl(number, control, min, max);
		return "";
	});
	registerCommand("control_listen_start", "control", [this](std::stringstream& ss)->std::string{
		if(peek(ss, 1)=="?") return
			"Listen for MIDI controller events, to be committed with control_listen_set.\n"
			"Make sure to send the full range of values with the controller you're mapping.";
		std::string s;
		ss>>s;
		if(_nameToControl.count(s)){
			_listening=s;
			_listeningControls.clear();
			return "listening";
		}
		return "error: no such control";
	});
	registerCommand("control_listen_set", "", [this](std::stringstream& ss)->std::string{
		if(peek(ss, 1)=="?") return
			"After control_listen_start is called and a MIDI controller events are sent, this function commits the mapping.";
		if(_listeningControls.size()){
			auto a=_listeningControls.begin();
			int control=a->first;
			int min=a->second._min;
			int max=a->second._max;
			int maxRange=a->second;
			if(control==int(PretendControl::PITCH_WHEEL)) maxRange>>=7;
			for(auto i: _listeningControls) if(i.second>maxRange){
				if(i.first==int(PretendControl::PITCH_WHEEL)&&i.second>>7<=maxRange) continue;
				control=i.first;
				min=i.second._min;
				max=i.second._max;
				maxRange=i.second;
			}
			addControl(control, _listening, min, max);
			_listening.clear();
			return "control "+std::to_string(control)+" range "+std::to_string(min)+".."+std::to_string(max);
		}
		else return "error: nothing to commit";
		return "";
	});
	registerCommand("control_listen_abort", "", [this](std::stringstream& ss)->std::string{
		if(peek(ss, 1)=="?") return
			"After control_listen_start is called, abort a mapping with this function.";
		_listening.clear();
		_listeningControls.clear();
		return "";
	});
	registerCommand("control_function", "control y[1]..y[n]", [this](std::stringstream& ss)->std::string{
		if(peek(ss, 1)=="?") return
			"By default, the MIDI controller values are mapped to the range [0, 1].\n"
			"A piecewise linear function with equally divided pieces can be described with this function.";
		std::string s;
		ss>>s;
		for(auto& i: _controls) if(i.second._name==s){
			i.second._f.clear();
			float f;
			while(ss>>f) i.second._f.push_back(f);
			if(i.second._f.empty()) return ::str(i.second._f);
			return "";
		}
		return "error: invalid or unmapped control";
	});
	registerCommand("control_list", "", [this](std::stringstream&){
		std::string result;
		for(auto i: _nameToControl) result+=i.first+"\n";
		return result;
	});
	registerCommand("control_clear", "control", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		for(auto& i: _controls) if(i.second._name==s){
			i.second._control=nullptr;
			return "";
		}
		return "error: unknown control";
	});
	registerCommand("serialize_midi_controllee", "", [this](std::stringstream& ss){
		return ::str(_controls);
	});
	registerCommand("deserialize_midi_controllee", "<serialized>", [this](std::stringstream& ss){
		::dstr(ss, _controls);
		for(auto& i: _controls) i.second._control=_nameToControl.at(i.second._name);
		return "";
	});
}

void MidiControllee::midi(const uint8_t* bytes, unsigned size){
	if(size!=3) return;
	int value, controller;
	switch(bytes[0]&0xf0){
		case 0xb0:
			value=bytes[2];
			controller=bytes[1];
			break;
		case 0xe0:
			value=(bytes[2]<<7)+bytes[1];
			controller=int(PretendControl::PITCH_WHEEL);
			break;
		default: return;
	}
	if(_listening.size()) _listeningControls[controller].value(value);
	if(!_controls.count(controller)) return;
	Control& control=_controls.at(controller);
	float f=1.0f*(value-control._min)/(control._max-control._min)*(control._f.size()-1);
	int i=int(f);
	float j=f-i;
	if(i>=(int)control._f.size()-1) *control._control=control._f.back();
	else if(i<0) *control._control=control._f.front();
	else *control._control=(1-j)*control._f[i]+j*control._f[i+1];
}

void MidiControllee::Range::value(int v){
	if(_new){
		_min=_max=v;
		_new=false;
		return;
	}
	if     (v<_min) _min=v;
	else if(v>_max) _max=v;
}

std::string MidiControllee::Control::str() const {
	return ::str(_name, _min, _max, _f);
}

void MidiControllee::Control::dstr(std::stringstream& ss){
	_f.clear();
	::dstr(ss, _name, _min, _max, _f);
}

void MidiControllee::addControl(int number, std::string name, int min, int max){
	_controls[number]._min=min;
	_controls.at(number)._max=max;
	_controls.at(number)._control=_nameToControl[name];
	_controls.at(number)._name=name;
}

}//namespace dlal
