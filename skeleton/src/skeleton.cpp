#include "skeleton.hpp"

#include <cstring>
#include <cstdlib>
#include <algorithm>

void dlalDemolishComponent(void* component){
	delete dlal::toComponent(component);
}

void* dlalBuildSystem(){ return new dlal::System; }

void dlalDemolishSystem(void* system){
	delete (dlal::System*)system;
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

//=====System=====//
std::string System::add(Component& component, unsigned slot, bool queue){
	std::string r=component.join(*this);
	if(isError(r)) return r;
	if(_components.size()<=slot) _components.resize(slot+1);
	if(queue){
		if(_componentsToAdd.size()<=slot) _componentsToAdd.resize(slot+1);
		_componentsToAdd[slot].push_back(&component);
	}
	else
		_components[slot].push_back(&component);
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
