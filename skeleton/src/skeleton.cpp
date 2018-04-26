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

static void atPanic(const char* message){
	std::cerr<<message<<"\n";
	throw std::runtime_error(message);
}

static void dyadWrite(dyad_Stream* stream, const uint8_t* data, uint32_t size){
	uint8_t s[4];
	s[0]=(size>>0x00)&0xff;
	s[1]=(size>>0x08)&0xff;
	s[2]=(size>>0x10)&0xff;
	s[3]=(size>>0x18)&0xff;
	dyad_write(stream, s, 4);
	dyad_write(stream, data, size);
}

static std::atomic<bool> dyadDone;
static std::thread dyadThread;
static std::recursive_mutex dyadMutex;

extern "C" {

DLAL void dlalDemolishComponent(void* component){
	delete dlal::toComponent(component);
}

DLAL void dlalDyadInit(){
	dyadMutex.lock();
	dyad_atPanic(atPanic);
	dyad_init();
	dyad_setUpdateTimeout(0.0);
	dyad_setTickInterval(0.01);
	dyadDone=false;
	dyadThread=std::thread([](){
		while(!dyadDone){
			dyadMutex.lock();
			dyad_update();
			dyadMutex.unlock();
			std::this_thread::sleep_for(std::chrono::milliseconds(1));
		}
	});
	dyadMutex.unlock();
}

DLAL void dlalDyadShutdown(){
	dyadDone=true;
	dyadThread.join();
	dyadMutex.lock();
	dyad_shutdown();
	dyadMutex.unlock();
}

DLAL void* dlalBuildSystem(int port, dlal::TextCallback pythonHandler){
	try{ return new dlal::System(port, pythonHandler); }
	catch(const std::exception& e){
		std::cerr<<e.what()<<"\n";
		return NULL;
	}
}

DLAL void dlalDemolishSystem(void* system){
	delete (dlal::System*)system;
}

DLAL void dlalReport(void* system, const char* report){
	dyadMutex.lock();
	((dlal::System*)system)->dyadWrite(report);
	dyadMutex.unlock();
}

DLAL void* dlalComponentWithName(void* system, const char* name){
	return ((dlal::System*)system)->_nameToComponent.at(name);
}

DLAL void dlalRename(void* system, void* component, const char* newName){
	using namespace dlal;
	((System*)system)->rename(toComponent(component), newName);
}

DLAL char* dlalSetVariable(void* system, const char* name, const char* value){
	return dlal::toCStr(((dlal::System*)system)->setVariable(name, value));
}

DLAL char* dlalCommand(void* component, const char* command){
	using namespace dlal;
	return toCStr(toComponent(component)->command(command));
}

DLAL char* dlalAdd(void* system, void* component, unsigned slot){
	using namespace dlal;
	return toCStr(((System*)system)->add(*toComponent(component), slot));
}

DLAL char* dlalConnect(void* input, void* output){
	using namespace dlal;
	return toCStr(toComponent(input)->connect(*toComponent(output)));
}

DLAL char* dlalDisconnect(void* input, void* output){
	using namespace dlal;
	return toCStr(toComponent(input)->disconnect(*toComponent(output)));
}

DLAL void* dlalSystem(void* component){
	using namespace dlal;
	return toComponent(component)->_system;
}

DLAL char* dlalSerialize(void* system){
	using namespace dlal;
	return toCStr(((System*)system)->serialize());
}

DLAL void dlalFree(void* p){ free(p); }

DLAL void dlalTest(){
	dlal::AtomicList<int>::test();
}

}//extern "C"

std::ostream& operator<<(std::ostream& ostream, const dlal::Component* component){
	return ostream<<componentToStr(component);
}

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

bool dataToStringstream(Queue<uint8_t>& data, std::stringstream& ss){
	uint8_t sizeBytes[4];
	if(!data.read(sizeBytes, 4, false)) return false;
	uint32_t size=
		(sizeBytes[0]<<0x00)|
		(sizeBytes[1]<<0x08)|
		(sizeBytes[2]<<0x10)|
		(sizeBytes[3]<<0x18)
	;
	if(!data.read(nullptr, size, false)) return false;
	data.read(nullptr, 4, true);
	std::vector<uint8_t> payload;
	payload.resize(size);
	data.read(payload.data(), size, true);
	for(unsigned i=0; i<size; ++i) ss<<(char)payload[i];
	return true;
}

//=====System=====//
static void onDestroyed(dyad_Event* e){
	System* system=(System*)e->udata;
	if(e->stream==system->_server) std::cerr<<"error: server destroyed"<<std::endl;
	else erase(e->stream, system->_clients);
}

static void onError(dyad_Event* e){
	System* system=(System*)e->udata;
	std::cerr<<"error: dyad error: "<<e->msg<<std::endl;
}

static void onData(dyad_Event* e){
	System* system=(System*)e->udata;
	system->_data.write((uint8_t*)e->data, e->size);
	std::stringstream ss;
	while(dataToStringstream(system->_data, ss))
		system->_pythonHandler(ss.str().c_str());
}

static void onAccept(dyad_Event* e){
	System* system=(System*)e->udata;
	system->_clients.push_back(e->remote);
	dyad_addListener(e->remote, DYAD_EVENT_DESTROY, onDestroyed, system);
	dyad_addListener(e->remote, DYAD_EVENT_ERROR, onError, system);
	dyad_addListener(e->remote, DYAD_EVENT_DATA, onData, system);
	std::stringstream ss;
	for(auto i: system->_components) for(auto j: i){
		ss<<"add "<<componentToStr(j)<<" "<<j->type()<<" ";
		if(j->_label.size()) ss<<"label "<<componentToStr(j)<<" "<<j->_label<<" ";
	}
	for(auto i: system->_reportConnections)
		ss<<"connect "<<i.first<<" "<<i.second<<" ";
	for(auto i: system->_variables)
		ss<<"variable "<<i.first<<"\n"<<i.second<<"\n";
	dyadWrite(e->remote, (uint8_t*)ss.str().data(), ss.str().size());
}

static void onTick(dyad_Event* e){
	System* system=(System*)e->udata;
	std::string s;
	std::stringstream ss;
	while(system->_reportQueue.read(s, true)){
		ss<<s<<" ";
		std::stringstream tt(s);
		std::string t;
		tt>>t;
		if(t=="connect"){
			tt>>t;
			std::string u;
			tt>>u;
			system->_reportConnections.push_back(
				std::pair<std::string, std::string>(t, u)
			);
		}
		else if(t=="disconnect"){
			tt>>t;
			std::string u;
			tt>>u;
			for(unsigned i=0; i<system->_reportConnections.size(); ++i)
				if(
					system->_reportConnections[i].first==t
					&&
					system->_reportConnections[i].second==u
				){
					system->_reportConnections.erase(
						system->_reportConnections.begin()+i
					);
					break;
				}
		}
	}
	if(ss.str().size()) system->dyadWrite(ss.str());
}

System::System(int port, TextCallback pythonHandler):
	_reportQueue(8),
	_data(10),
	_pythonHandler(pythonHandler),
	_dyadDone(dyadDone),
	_dyadMutex(dyadMutex)
{
	if(port){
		_dyadNewStream=dyad_newStream;
		_dyadAddListener=dyad_addListener;
		_dyadListenEx=dyad_listenEx;
		std::string r=dyadPauseAnd([&]()->std::string{
			_server=dyad_newStream();
			dyad_addListener(_server, DYAD_EVENT_ACCEPT , onAccept   , this);
			dyad_addListener(_server, DYAD_EVENT_ERROR  , onError    , this);
			dyad_addListener(_server, DYAD_EVENT_DESTROY, onDestroyed, this);
			dyad_addListener(_server, DYAD_EVENT_TICK   , onTick     , this);
			if(dyad_listenEx(_server, "0.0.0.0", port, 511)<0){
				std::stringstream ss;
				ss<<"error: constructing System, couldn't listen on port "<<port;
				return ss.str();
			}
			return "";
		});
		if(r.size()) throw std::runtime_error(r);
	}
	else _server=nullptr;
}

System::~System(){
	if(_server){
		dyadPauseAnd([this]()->std::string{
			for(auto i: _clients) dyad_removeAllListeners(i, DYAD_EVENT_NULL);
			dyad_close(_server);
			dyad_removeAllListeners(_server, DYAD_EVENT_NULL);
			for(auto i: _streams) dyad_removeAllListeners(i, DYAD_EVENT_NULL);
			return "";
		});
	}
}

std::string System::add(Component& component, unsigned slot, bool queue){
	for(auto i: _components) for(auto j: i) if(j==&component) return "error: already added";
	std::string r=component.join(*this);
	if(isError(r)) return r;
	if(_components.size()<=slot) _components.resize(slot+1);
	if(queue){
		if(_componentsToAdd.size()<=slot) _componentsToAdd.resize(slot+1);
		_componentsToAdd[slot].push_back(&component);
	}
	else _components[slot].push_back(&component);
	_nameToComponent[component._name]=&component;
	_reportQueue.write("add "+componentToStr(&component)+" "+component.type());
	return "";
}

std::string System::remove(Component& component, bool queue){
	for(auto i: _components){
		auto j=std::find(i.begin(), i.end(), &component);
		if(j!=i.end()){
			if(queue) _componentsToRemove.push_back(&component);
			else i.erase(j);
			_reportQueue.write("remove "+componentToStr(&component));
			return "";
		}
	}
	return "error: component was not added";
}

std::string System::check(){
	std::set<std::string> components;
	for(auto connection: _reportConnections){
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
	for(auto i: _componentsToRemove) remove(*i);
	_componentsToRemove.clear();
	if(_components.size()<_componentsToAdd.size())
		_components.resize(_componentsToAdd.size());
	for(unsigned i=0; i<_componentsToAdd.size(); ++i)
		_components[i].insert(
			_components[i].end(),
			_componentsToAdd[i].begin(), _componentsToAdd[i].end()
		);
	_componentsToAdd.clear();
	for(auto i: _components) for(auto j: i) j->evaluate();
}

std::string System::set(unsigned sampleRate, unsigned log2SamplesPerCallback){
	if(!sampleRate||!log2SamplesPerCallback)
		return "error: must set sample rate and log2 samples per callback";
	_variables["sampleRate"]=std::to_string(sampleRate);
	_variables["samplesPerEvaluation"]=std::to_string(1<<log2SamplesPerCallback);
	return "";
}

std::string System::setVariable(std::string name, std::string value){
	if(std::string(name ).find('\n')!=std::string::npos)
		return "error: name cannot contain newline";
	if(std::string(value).find('\n')!=std::string::npos)
		return "error: value cannot contain newline";
	_variables[name]=value;
	_reportQueue.write("variable "+name+"\n"+value+"\n");
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
	ss<<"\"connections\": "<<_reportConnections<<"\n";
	ss<<"}\n";
	return ss.str();
}

void System::rename(Component* component, const char* newName){
	for(auto& i: _reportConnections){
		if(i.first==component->_name) i.first=newName;
		if(i.second==component->_name) i.second=newName;
	}
	component->_name=newName;
}

dyad_Stream* System::dyadNewStream(){
	dyad_Stream* r=_dyadNewStream();
	_streams.push_back(r);
	return r;
}

void System::dyadAddListener(
	dyad_Stream* stream, int event, dyad_Callback callback, void* userData
){
	_dyadAddListener(stream, event, callback, userData);
}

int System::dyadListenEx(
	dyad_Stream* stream, const char* host, int port, int backlog
){
	return _dyadListenEx(stream, host, port, backlog);
}

std::string System::dyadPauseAnd(std::function<std::string()> f){
	std::string r;
	_dyadMutex.lock();
	if(!_dyadDone) r=f();
	_dyadMutex.unlock();
	return r;
}

void System::dyadWrite(std::string s){
	dyadMutex.lock();
	for(auto i: _clients)
		::dyadWrite(i, (uint8_t*)s.data(), s.size());
	dyadMutex.unlock();
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
			_system->_reportQueue.write("label "+componentToStr(this)+" "+_label);
			return "";
		}
		return "error: no system";
	});
	registerCommand("midi", "byte[1]..byte[n]", [this](std::stringstream& ss){
		if(!midiAccepted()) return "error: midi not accepted";
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
		tt<<(Periodic*)this;
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
		if(!isError(s)) _last=0.0f;
		return s;
	});
	registerCommand("periodic_match", "<other periodic>", [this](std::stringstream& ss){
		void* v;
		ss>>v;
		auto other=(Periodic*)v;
		auto s=resize(other->_period);
		if(isError(s)) return s;
		s=setPhase(other->_phase);
		if(!isError(s)) _last=0.0f;
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

std::string Periodic::setPhase(uint64_t phase){ _phase=phase; return ""; }

bool Periodic::phase(){
	_phase+=_samplesPerEvaluation;
	if(_phase<_period){
		float current=1.0f*_phase/_period;
		if(current-_last>0.01f){
			_system->_reportQueue.write((std::string)"phase "+componentToStr(this)+" "+std::to_string(current));
			_last=current;
		}
		return false;
	}
	_phase-=_period;
	_system->_reportQueue.write((std::string)"edge "+componentToStr(this));
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
		if(ss.str().size()) system._reportQueue.write(ss.str());
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
	_outputs.push_back(&output);
	if(_system) _system->_reportQueue.write(
		"connect "+componentToStr(this)+" "+componentToStr(&output)
	);
	return "";
}

std::string MultiOut::disconnect(Component& output){
	auto i=std::find(_outputs.begin(), _outputs.end(), &output);
	if(i==_outputs.end()) return "error: component was not connected";
	_outputs.erase(i);
	if(_system) _system->_reportQueue.write(
		"disconnect "+componentToStr(this)+" "+componentToStr(&output)
	);
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
