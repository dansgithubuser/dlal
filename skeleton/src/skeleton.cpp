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
	dyad_setTickInterval(0.01);
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

void dlalSetVariable(void* system, const char* name, const char* value){
	dlal::System* s=(dlal::System*)system;
	s->_variables[name]=value;
	s->_reportQueue.write((std::string)"variable "+name+" "+value);
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

Component* toComponent(void* p){ return (Component*)p; }

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
static std::string pointerToString(const void* pointer){
	std::stringstream ss;
	ss<<(uint64_t)pointer;
	return ss.str();
}

static std::string componentToStr(const Component* component){
	return pointerToString(component);
}

static void onDestroyed(dyad_Event* e){
	System* system=(System*)e->udata;
	system->report(System::RC_IN_DYAD, "error: server destroyed");
}

static void onError(dyad_Event* e){
	System* system=(System*)e->udata;
	system->report(System::RC_IN_DYAD, "error: "+std::string(e->msg));
}

static void onAccept(dyad_Event* e){
	System* system=(System*)e->udata;
	system->_clients.push_back(e->remote);
	std::stringstream ss;
	for(auto i: system->_components) for(auto j: i)
		ss<<"add "<<componentToStr(j)<<" "<<j->type()<<" ";
	for(auto i: system->_reportConnections)
		ss<<"connect "<<i.first<<" "<<i.second<<" ";
	for(auto i: system->_variables)
		ss<<"variable "<<i.first<<" "<<i.second<<" ";
	dyad_write(e->remote, ss.str().data(), ss.str().size());
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
	if(ss.str().size())
		for(auto i: system->_clients)
			dyad_write(i, ss.str().data(), ss.str().size());
}

System::System(int port): _reportQueue(8){
	_dyadNewStream=dyad_newStream;
	_dyadAddListener=dyad_addListener;
	_dyadListenEx=dyad_listenEx;
	for(unsigned i=0; i<RC_SENTINEL; ++i) _report[i].reserve(16);
	std::string r=dyadPauseAnd([&]()->std::string{
		_server=dyad_newStream();
		dyad_addListener(_server, DYAD_EVENT_ACCEPT , onAccept   , this);
		dyad_addListener(_server, DYAD_EVENT_ERROR  , onError    , this);
		dyad_addListener(_server, DYAD_EVENT_DESTROY, onDestroyed, this);
		dyad_addListener(_server, DYAD_EVENT_TICK   , onTick     , this);
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
	if(_variables.count("sampleRate"))
		return "error: system already has sampleRate";
	if(_variables.count("samplesPerEvaluation"))
		return "error: system already has samplesPerEvaluation";
	_variables["sampleRate"]=std::to_string(sampleRate);
	_variables["samplesPerEvaluation"]=std::to_string(1<<log2SamplesPerCallback);
	return "";
}

std::string System::report(
	ReportContext rc, const std::string& s, const Component* reporter
){
	if(s.size()){
		std::stringstream ss;
		ss<<pointerToString(reporter)<<": "<<s;
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

//=====SamplesPerEvaluationGetter=====//
SamplesPerEvaluationGetter::SamplesPerEvaluationGetter(){
	addJoinAction([this](System& system){
		if(!system._variables.count("samplesPerEvaluation"))
			return "error: system does not have samplesPerEvaluation";
		_samplesPerEvaluation=std::stoi(system._variables["samplesPerEvaluation"]);
		return "";
	});
}

//=====SampleRateGetter=====//
SampleRateGetter::SampleRateGetter(){
	addJoinAction([this](System& system){
		if(!system._variables.count("sampleRate"))
			return "error: system does not have sampleRate";
		_sampleRate=std::stoi(system._variables["sampleRate"]);
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

}//namespace dlal
