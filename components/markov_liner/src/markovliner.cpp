#include "markovliner.hpp"

#include <obvious.hpp>

#include <ctime>

DLAL_BUILD_COMPONENT_DEFINITION(MarkovLiner)

static std::ostream& operator<<(std::ostream& s, const dlal::MarkovLiner::State& x) {
	return s<<x.on<<" "<<x.off<<" "<<x.duration;
}

static std::istream& operator>>(std::istream& s, dlal::MarkovLiner::State& x) {
	return s>>x.on>>" ">>x.off>>" ">>x.duration;
}

static std::ostream& operator<<(std::ostream& s, const dlal::MarkovLiner::Transition& x) {
	return s<<x.weight<<" "<<x.state;
}

static std::istream& operator>>(std::istream& s, dlal::MarkovLiner::Transition& x) {
	return s>>x.weight>>" ">>x.state;
}

namespace dlal{

MarkovLiner::MarkovLiner(){
	_checkMidi=true;
	_rng.seed(std::time(NULL)+(size_t)this);
	_rng();
	registerCommand("serialize_markov_liner", "", [this](std::stringstream&){
		std::stringstream ss;
		ss<<_states<<" "<<_transitions;
		return ss.str();
	});
	registerCommand("deserialize_markov_liner", "<serialized>", [this](std::stringstream& ss){
		ss>>_states>>" ">>_transitions;
		return "";
	});
	registerCommand("state_create", "<on midi bytes> ; <off midi bytes> ; duration", [this](std::stringstream& ss){
		std::string s;
		State state;
		while(ss>>s){
			if(s==";") break;
			state.on.push_back(std::stoul(s));
		}
		while(ss>>s){
			if(s==";") break;
			state.off.push_back(std::stoul(s));
		}
		ss>>state.duration;
		_states.push_back(state);
		return std::to_string(_states.size()-1);
	});
	registerCommand("transition_create", "initial final weight", [this](std::stringstream& ss){
		size_t i;
		Transition t;
		ss>>i>>t.state>>t.weight;
		if(i>=_states.size()) return "error: no such initial state";
		if(t.state>=_states.size()) return "error: no such final state";
		_transitions[i].push_back(t);
		return "";
	});
}

void MarkovLiner::evaluate(){
	if(phase()){
		_mainState=WAITING;
		_stateAge=0;
	}
	if(_mainState==WAITING&&_states.size()){
		becomeState(0);
		_mainState=PLAYING;
	}
	if(_mainState==PLAYING){
		if(_stateAge>=_states[_state].duration) becomeState(selectState());
		_stateAge+=_samplesPerEvaluation;
	}
}

void MarkovLiner::becomeState(size_t state){
	if(_mainState!=WAITING){
		_stateAge-=_states[_state].duration;
		for(auto output: _outputs){
			midiSend(output, _states[_state].off.data(), _states[_state].off.size());
		}
	}
	_state=state;
	if(_mainState!=DONE){
		for(auto output: _outputs){
			midiSend(output, _states[_state].on.data(), _states[_state].on.size());
		}
	}
}

size_t MarkovLiner::selectState(){
	if(!_transitions.count(_state)){
		_mainState=DONE;
		return 0;
	}
	auto& transitions=_transitions.at(_state);
	float x=1.0f*(_rng()-_rng.min())/(_rng.max()-_rng.min());
	for(const auto& i: transitions){
		x-=i.weight;
		if(x<=0.001f) return i.state;
	}
	_mainState=DONE;
	return 0;
}

}//namespace dlal
