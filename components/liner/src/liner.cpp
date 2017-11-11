#include "liner.hpp"

#include "midi.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Liner; }

namespace dlal{

Liner::Liner(): _resetOnMidi(false) {
	_iterator=_line.begin();
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
	registerCommand("save", "<file path> <samples per quarter>", [this](std::stringstream& ss){
		std::string file_path;
		ss>>file_path;
		float samples_per_quarter;
		ss>>samples_per_quarter;
		dlal::Midi m;
		uint64_t last=0;
		for(auto i: _line){
			auto delta=uint32_t((i.sample-last)/samples_per_quarter*m.ticksPerQuarter);
			m.append(1, delta, i.midi);
			last=i.sample;
		}
		m.write(file_path);
		return "";
	});
	registerCommand("load", "<file path> <samples per quarter>", [this](std::stringstream& ss){
		std::string file_path;
		ss>>file_path;
		float samples_per_quarter;
		ss>>samples_per_quarter;
		dlal::Midi m;
		m.read(file_path);
		int ticks=0;
		if(m.tracks.size()<2) return "error: no track to read";
		auto pairs=getPairs(m.tracks[1]);
		_line.clear();
		for(auto i: pairs){
			ticks+=i.delta;
			_line.push_back(Midi{uint64_t(ticks*samples_per_quarter/m.ticksPerQuarter), i.event});
		}
		return "";
	});
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
	while(_iterator&&_iterator->sample<=_phase){
		for(auto output: _outputs){
			std::vector<uint8_t>& m=_iterator->midi;
			output->midi(m.data(), m.size());
			_system->_reportQueue.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(output));
		}
		++_iterator;
	}
	//move forward
	if(phase()) _iterator=_line.begin();
}

void Liner::midi(const uint8_t* bytes, unsigned size){
	if(_resetOnMidi){
		_phase=0;
		_iterator=_line.begin();
		_resetOnMidi=false;
	}
	put(bytes, size, _phase);
}

std::string Liner::setPhase(uint64_t phase){
	Periodic::setPhase(phase);
	_iterator=_line.begin();
	while(_iterator&&_iterator->sample<_phase) ++_iterator;
	return "";
}

void Liner::put(const uint8_t* midi, unsigned size, uint64_t sample){
	Midi m{sample, std::vector<uint8_t>(midi, midi+size)};
	auto i=_line.begin();
	for(/*nothing*/; i!=_line.end(); ++i) if(i->sample>=sample) break;
	_line.insert(i, m);
	if(!_iterator) setPhase(_phase);
}

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Liner::Midi& midi){
	return o<<"{"<<midi.sample<<", "<<midi.midi<<"}";
}
