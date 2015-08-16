#include "skeleton.hpp"

#include <algorithm>
#include <atomic>
#include <cstring>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <thread>

void dlalDemolishComponent(void* component){
	delete dlal::toComponent(component);
}

static void atPanic(const char* message){
	std::cerr<<message<<"\n";
	throw std::runtime_error(message);
}

static std::atomic<bool> dyadDone;
static std::thread dyadThread;
static std::mutex dyadMutex;

void dlalDyadInit(){
	dyadMutex.lock();
	dyad_atPanic(atPanic);
	dyad_init();
	dyad_setUpdateTimeout(0.01);
	dyadDone=false;
	dyadThread=std::thread([](){
		while(!dyadDone){
			dyadMutex.lock();
			dyad_update();
			dyadMutex.unlock();
		}
	});
	dyadMutex.unlock();
}

void dlalDyadShutdown(){
	dyadDone=true;
	dyadThread.join();
	dyadMutex.lock();
	dyad_shutdown();
	dyadMutex.unlock();
}

void* dlalBuildSystem(int port){
	try{ return new dlal::System(port); }
	catch(const std::exception& e){
		std::cerr<<e.what()<<"\n";
		return NULL;
	}
}

char* dlalDemolishSystem(void* system){
	using namespace dlal;
	std::string result=((System*)system)->report();
	delete (System*)system;
	return toCStr(result);
}

char* dlalCommand(void* component, const char* command){
	using namespace dlal;
	return toCStr(toComponent(component)->command(command));
}

char* dlalAdd(void* system, void* component, unsigned slot){
	using namespace dlal;
	return toCStr(((System*)system)->add(*toComponent(component), slot));
}

char* dlalConnect(void* input, void* output){
	using namespace dlal;
	return toCStr(toComponent(input)->connect(*toComponent(output)));
}

char* dlalDisconnect(void* input, void* output){
	using namespace dlal;
	return toCStr(toComponent(input)->disconnect(*toComponent(output)));
}

namespace dlal{

Component* toComponent(void* p){ return (dlal::Component*)p; }

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

std::string dyadPauseAnd(std::function<std::string()> f){
	dyadMutex.lock();
	std::string r=f();
	dyadMutex.unlock();
	return r;
}

//=====System=====//
static void onDestroyed(dyad_Event* e){
	dlal::System* system=((dlal::System*)e->udata);
	system->report(System::RC_IN_DYAD, "error: server destroyed");
}

static void onError(dyad_Event* e){
	dlal::System* system=((dlal::System*)e->udata);
	system->report(System::RC_IN_DYAD, "error: "+std::string(e->msg));
}

static void onAccept(dyad_Event* e){
	dlal::System* system=((dlal::System*)e->udata);
	system->_clients.push_back(e->remote);
}

System::System(int port){
	_dyadNewStream=dyad_newStream;
	_dyadAddListener=dyad_addListener;
	_dyadListenEx=dyad_listenEx;
	for(unsigned i=0; i<RC_SENTINEL; ++i) _report[i].reserve(16);
	std::string r=dyadPauseAnd([&]()->std::string{
		_server=dyad_newStream();
		dyad_addListener(_server, DYAD_EVENT_ACCEPT , onAccept   , this);
		dyad_addListener(_server, DYAD_EVENT_ERROR  , onError    , this);
		dyad_addListener(_server, DYAD_EVENT_DESTROY, onDestroyed, this);
		if(dyad_listenEx(_server, "0.0.0.0", port, 511)<0)
			return "error: couldn't listen";
		return "";
	});
	if(r.size()) throw std::runtime_error(r);
}

System::~System(){
	dyadPauseAnd([this]()->std::string{
		dyad_close(_server);
		dyad_removeListener(_server, DYAD_EVENT_ACCEPT , onAccept   , this);
		dyad_removeListener(_server, DYAD_EVENT_ERROR  , onError    , this);
		dyad_removeListener(_server, DYAD_EVENT_DESTROY, onDestroyed, this);
		for(auto i: _streams) dyad_removeAllListeners(i, DYAD_EVENT_DESTROY);
		return "";
	});
}

std::string System::add(Component& component, unsigned slot, bool queue){
	std::string r=component.join(*this);
	if(isError(r)) return r;
	if(_components.size()<=slot) _components.resize(slot+1);
	if(queue){
		if(_componentsToAdd.size()<=slot) _componentsToAdd.resize(slot+1);
		_componentsToAdd[slot].push_back(&component);
	}
	else _components[slot].push_back(&component);
	return "";
}

std::string System::remove(Component& component, bool queue){
	for(auto i: _components){
		auto j=std::find(i.begin(), i.end(), &component);
		if(j!=i.end()){
			if(queue) _componentsToRemove.push_back(&component);
			else i.erase(j);
			return "";
		}
	}
	return "error: component was not added";
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

bool System::set(std::string variable, unsigned value){
	bool result=_variables.count(variable)!=0;
	_variables[variable]=std::to_string(value);
	return result;
}

std::string System::report(
	ReportContext rc, const std::string& s, const Component* reporter
){
	if(s.size()){
		std::stringstream ss;
		ss<<(uint64_t)reporter<<": "<<s;
		_report[(unsigned)rc].push_back(ss.str());
		return dyadPauseAnd([&]()->std::string{
			std::vector<uint8_t> bytes;
			unsigned size=ss.str().size();
			bytes.resize(4+size);
			bytes[0]=(size>>0x00)&0xff;
			bytes[1]=(size>>0x08)&0xff;
			bytes[2]=(size>>0x10)&0xff;
			bytes[3]=(size>>0x18)&0xff;
			for(unsigned i=0; i<size; ++i) bytes[4+i]=ss.str()[i];
			for(auto client: _clients)
				dyad_write(client, bytes.data(), bytes.size());
			return "";
		});
	}
	else{
		std::string result;
		for(unsigned i=0; i<RC_SENTINEL; ++i){
			if(!_report[i].size()) continue;
			switch(i){
				case RC_IN_EVALUATION: result+="---in evaluation---\n"; break;
				case RC_IN_DYAD:       result+="---in dyad---\n";       break;
			}
			for(auto j: _report[i]) result+=j+"\n";
		}
		return result;
	}
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

bool System::get(std::string variable, unsigned* value){
	if(!_variables.count(variable)) return false;
	if(value) *value=std::atoi(_variables[variable].c_str());
	return true;
}

std::string System::set(unsigned sampleRate, unsigned log2SamplesPerCallback){
	if(!sampleRate||!log2SamplesPerCallback)
		return "error: must set sample rate and log2 samples per callback";
	if(get("sampleRate"))
		return "error: system already has sampleRate";
	if(get("samplesPerEvaluation"))
		return "error: system already has samplesPerEvaluation";
	set("sampleRate", sampleRate);
	set("samplesPerEvaluation", 1<<log2SamplesPerCallback);
	return "";
}

//=====Component=====//
Component::Component(){
	registerCommand("help", "", [this](std::stringstream& ss){
		std::string result="recognized commands are:\n";
		for(auto i: _commands) result+=i.first+" "+i.second.parameters+"\n";
		return result;
	});
}

std::string Component::command(const std::string& command){
	std::stringstream ss(command);
	std::string s;
	ss>>s;
	if(!_commands.count(s))
		return "error: "+s+" unrecognized\n"+_commands["help"].command(ss);
	return _commands[s].command(ss);
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

void Component::addJoinAction(JoinAction j){ _joinActions.push_back(j); }

//=====MultiOut=====//
MultiOut::MultiOut(): _checkAudio(false), _checkMidi(false) {}

std::string MultiOut::connect(Component& output){
	if(_checkAudio&&!output.hasAudio())
		return "error: output must have audio";
	if(_checkMidi&&!output.midiAccepted())
		return "error: output must accept midi";
	if(std::find(_outputs.begin(), _outputs.end(), &output)!=_outputs.end())
		return "error: output already connected";
	_outputs.push_back(&output);
	return "";
}

std::string MultiOut::disconnect(Component& output){
	auto i=std::find(_outputs.begin(), _outputs.end(), &output);
	if(i==_outputs.end()) return "error: component was not connected";
	_outputs.erase(i);
	return "";
}

//=====SamplesPerEvaluationGetter=====//
SamplesPerEvaluationGetter::SamplesPerEvaluationGetter(){
	addJoinAction([this](System& system){
		if(!system.get("samplesPerEvaluation", &_samplesPerEvaluation))
		return "error: system does not have samplesPerEvaluation";
		return "";
	});
}

//=====SampleRateGetter=====//
SampleRateGetter::SampleRateGetter(){
	addJoinAction([this](System& system){
		if(!system.get("sampleRate", &_sampleRate))
		return "error: system does not have sampleRate";
		return "";
	});
}

//=====SystemGetter=====//
SystemGetter::SystemGetter(): _system(nullptr) {
	addJoinAction([this](System& system){
		_system=&system;
		return "";
	});
}

}//namespace dlal
