#include "liner.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Liner; }

namespace dlal{

Liner::Liner(): _index(0), _resetOnMidi(false) {
	_checkMidi=true;
	addJoinAction([this](System&){
		if(!_period) return "error: size not set";
		return "";
	});
	registerCommand("midi_event", "<time in samples> byte[1]..byte[n]",
		[this](std::stringstream& ss){
			unsigned sample;
			ss>>sample;
			std::vector<uint8_t> m;
			unsigned byte;
			while(ss>>byte) m.push_back(byte);
			put(m.data(), m.size(), sample);
			return "";
		}
	);
	registerCommand("clear", "", [this](std::stringstream& ss){
		_line.clear();
		return "";
	});
	registerCommand("reset_on_midi", "", [this](std::stringstream& ss){
		_resetOnMidi=true;
		return "";
	});
}

void Liner::evaluate(){
	//output
	while(_index<_line.size()&&_line[_index].sample<=_phase){
		for(auto output: _outputs){
			std::vector<uint8_t>& m=_line[_index].midi;
			output->midi(m.data(), m.size());
			_system->_reportQueue.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(output));
		}
		++_index;
	}
	//move forward
	if(phase()) _index=0;
}

void Liner::midi(const uint8_t* bytes, unsigned size){
	if(_resetOnMidi){
		_phase=0;
		_index=0;
		_resetOnMidi=false;
	}
	put(bytes, size, _phase);
}

void Liner::setPhase(uint64_t phase){
	Periodic::setPhase(phase);
	_index=0;
	while(_index<_line.size()&&_line[_index].sample<=_phase) ++_index;
}

Liner::Midi::Midi(uint64_t sample, const uint8_t* midi, unsigned size):
	sample(sample), midi(midi, midi+size)
{}

void Liner::put(const uint8_t* midi, unsigned size, uint64_t sample){
	Midi m(sample, midi, size);
	for(auto i=_line.begin(); i!=_line.end(); ++i)
		if(i->sample>=sample){
			_line.insert(i, m);
			return;
		}
	_line.push_back(m);
}

}//namespace dlal
