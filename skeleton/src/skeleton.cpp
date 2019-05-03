#include "skeleton.hpp"

#include "atomiclist.hpp"

#include <obvious.hpp>

#include <algorithm>
#include <cstring>
#include <cstdlib>
#include <iostream>
#include <set>
#include <stdexcept>
#include <thread>

std::ostream& operator<<(std::ostream& ostream, const dlal::Component* component){
	return ostream<<componentToStr(component);
}

std::istream& operator>>(std::istream& istream, dlal::Component*& component){
	void* v;
	istream>>v;
	component=(dlal::Component*)v;
	return istream;
}

extern "C" {

DLAL const char* dlalRequest(const char* request, bool immediate){
	static std::set<dlal::System*> systems;
	static dlal::System* active=nullptr;
	if(immediate){
		std::stringstream ss(request);
		static std::string s;
		ss>>s;
		if(s=="test"){
			dlal::AtomicList<int>::test();
		}
		else if(s=="system/build"){
			auto system=new dlal::System;
			systems.insert(system);
			s=obvstr(system);
		}
		else if(s=="system/switch"){
			s=obvstr(active);
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
		else if(s=="component/connect"){
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
		else if(s=="component/demolish"){
			dlal::Component* c;
			ss>>c;
			delete c;
		}
		else if(!active) return "error: no active system\n";
		else s=active->handleRequest(request);
		return s.c_str();
	}
	else if(!active) return "error: no active system\n";
	else{
		static int requestNumber=0;
		++requestNumber;
		active->_requests.write(std::to_string(requestNumber)+" "+request);
		return "";
	}
}

}//extern "C"

namespace dlal{

Component* toComponent(void* p){ return (Component*)p; }

std::string componentToStr(const Component* component){
	return component->_name;
}

char* toCStr(const std::string& s){
	char* result=(char*)malloc(s.size()+1);
	result[s.size()]='\0';
	memcpy(result, s.c_str(), s.size());
	return result;
}

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
	_reports.write("add "+componentToStr(&component)+" "+component.type());
	return "";
}

std::string System::remove(Component& component){
	for(auto i: _components){
		auto j=std::find(i.begin(), i.end(), &component);
		if(j!=i.end()){
			i.erase(j);
			_reports.write("remove "+componentToStr(&component));
			return "";
		}
	}
	return "error: component was not added";
}

std::string System::check(){
	std::set<std::string> components;
	for(auto connection: _connections){
		components.insert(connection.first);
		components.insert(connection.second);
	}
	for(auto slot: _components)
		for(auto component: slot)
			components.erase(componentToStr(component));
	if(components.size()) return "error: connected components have not been added";
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
	for(auto i: _components) for(auto j: i) j->evaluate();
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

std::string System::serialize() const {
	std::stringstream ss;
	ss<<"{\n";
	ss<<"\"variables\": "<<_variables<<",\n";
	ss<<"\"component_order\": "<<_components<<",\n";
	std::map<Component*, std::string> types, components;
	for(auto i: _components) for(auto j: i){
		types[j]=j->command("type");//can't call type function directly, causes segfault, not sure how this solves
		components[j]=j->command("serialize");
		replace(components[j], "\n", " ");
		replace(components[j], "\t", " ");
	}
	ss<<"\"component_types\": "<<types<<",\n";
	ss<<"\"components\": "<<components<<",\n";
	ss<<"\"connections\": "<<_connections<<"\n";
	ss<<"}\n";
	return ss.str();
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
	_reports.write(obvstr("rename", oldName, newName));
	return "";
}

std::string System::handleRequest(std::string request){
	std::stringstream ss(request);
	std::string command;
	ss>>command;
	std::string s;
	if(command=="system/report"){
		if(_reports.read(s, true)) return "value: "+s;
	}
	else if(command=="system/serialize") return serialize();
	else if(command=="variable/get"){
		if(ss>>s){
			if(!_variables.count(s)) return "error: no such variable";
			return "value: "+_variables.at(s);
		}
		else{
			std::stringstream ss;
			ss<<"value: "<<_variables;
			return ss.str();
		}
	}
	else if(command=="variable/set"){
		std::string name, value;
		ss>>name>>value;
		return setVariable(name, value);
	}
	else if(command=="variable/unset"){
		ss>>s;
		if(!_variables.count(s)) return "error: no such variable";
		_variables.erase(s);
	}
	else if(command=="component/get"){
		if(ss>>s){
			if(!_nameToComponent.count(s)) return "error: no such component";
			return obvstr(_nameToComponent.at(s));
		}
		else{
			std::stringstream ss;
			ss<<"value: ";
			for(const auto& i: _nameToComponent) ss<<i.first<<" ";
			return ss.str();
		}
	}
	else if(command=="component/get/connections"){
		std::stringstream ss;
		ss<<"value: ";
		ss<<_connections;
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
	else if(command=="component/rename"){
		Component* c;
		ss>>c>>s;
		return rename(*c, s);
	}
	else if(command=="component/connect"){
		Component* a;
		Component* b;
		ss>>a>>b;
		s=a->connect(*b);
		if(!isError(s)){
			auto sa=componentToStr(a);
			auto sb=componentToStr(b);
			_reports.write("connect "+sa+" "+sb);
			_connections.push_back(std::pair<std::string, std::string>(sa, sb));
		}
		return s;
	}
	else if(command=="component/disconnect"){
		Component* a;
		Component* b;
		ss>>a>>b;
		s=a->disconnect(*b);
		if(!isError(s)){
			auto sa=componentToStr(a);
			auto sb=componentToStr(b);
			_reports.write("disconnect "+sa+" "+sb);
			for(unsigned i=0; i<_connections.size(); ++i)
				if(_connections[i]==std::pair<std::string, std::string>(sa, sb)){
					_connections[i]=_connections.back();
					_connections.pop_back();
					break;
				}
		}
		return s;
	}
	else if(command=="component/command"){
		Component* c;
		ss>>c;
		std::getline(ss, s);
		return c->command(s);
	}
	else return "error: no such command";
	return "";
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
	registerCommand("to_str", "", [this](std::stringstream&){
		return componentToStr(this);
	});
	registerCommand("label", "<label>", [this](std::stringstream& ss){
		ss>>_label;
		if(_system){
			_system->_reports.write("label "+componentToStr(this)+" "+_label);
			return "";
		}
		return "error: no system";
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
		for(auto i: _commands) if(startsWith(i.first, "deserialize_"))
			i.second.command(ss);
		return "";
	});
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
	_system->_reports.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(target));
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
			_system->_reports.write((std::string)"phase "+componentToStr(this)+" "+std::to_string(current));
			_last=current;
		}
		return false;
	}
	_phase-=_period;
	_system->_reports.write((std::string)"edge "+componentToStr(this));
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
			ss<<"connect "+componentToStr(this)+" "+componentToStr(i)<<" ";
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
		return "error: output already connected";
	if(_maxOutputs&&_outputs.size()==_maxOutputs)
		return "error: max outputs already connected";
	_outputs.push_back(&output);
	return "";
}

std::string MultiOut::disconnect(Component& output){
	auto i=std::find(_outputs.begin(), _outputs.end(), &output);
	if(i==_outputs.end()) return "error: component was not connected";
	_outputs.erase(i);
	return "";
}

//=====MidiControllee=====//
MidiControllee::MidiControllee(): _listening(nullptr), _controls(int(PretendControl::SENTINEL)){
	registerCommand("control_set", "control number <min value> <max value>", [this](std::stringstream& ss){
		std::string control;
		int number, min, max;
		ss>>control>>number>>min>>max;
		if(!_nameToControl.count(control)) return "error: unknown control";
		if(number>127) return "error: controller number too high";
		_controls[number]._min=min;
		_controls[number]._max=max;
		_controls[number]._control=_nameToControl[control];
		return "";
	});
	registerCommand("control_listen_start", "control", [this](std::stringstream& ss)->std::string{
		std::string s;
		ss>>s;
		if(_nameToControl.count(s)){
			_listening=_nameToControl[s];
			_listeningControls.clear();
			return "listening";
		}
		return "error: no such control";
	});
	registerCommand("control_listen_set", "", [this](std::stringstream& ss)->std::string{
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
			_controls[control]._min=min;
			_controls[control]._max=max;
			_controls[control]._control=_listening;
			_listening=nullptr;
			return "control "+std::to_string(control)+" range "+std::to_string(min)+".."+std::to_string(max);
		}
		else return "error: nothing to commit";
		return "";
	});
	registerCommand("control_listen_abort", "", [this](std::stringstream& ss)->std::string{
		_listening=nullptr;
		_listeningControls.clear();
		return "";
	});
	registerCommand("control_function", "control y[1]..y[n]", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		for(auto& i: _controls) if(i._control==_nameToControl[s]){
			i._f.clear();
			float f;
			while(ss>>f) i._f.push_back(f);
			if(i._f.empty()){
				i._f.push_back(0.0f);
				i._f.push_back(1.0f);
			}
			return "";
		}
		return "error: unknown control";
	});
	registerCommand("control_list", "", [this](std::stringstream&){
		std::string result;
		for(auto i: _nameToControl) result+=i.first+"\n";
		return result;
	});
	registerCommand("control_clear", "control", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		for(auto& i: _controls) if(i._control==_nameToControl[s]){
			i._control=nullptr;
			return "";
		}
		return "error: unknown control";
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
	if(_listening) _listeningControls[controller].value(value);
	Control& control=_controls[controller];
	if(control._control){
		float f=1.0f*(value-control._min)/(control._max-control._min)*(control._f.size()-1);
		int i=int(f);
		float j=f-i;
		if(i>=(int)control._f.size()-1) *control._control=control._f.back();
		else if(i<0) *control._control=control._f.front();
		else *control._control=(1-j)*control._f[i]+j*control._f[i+1];
	}
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

}//namespace dlal
