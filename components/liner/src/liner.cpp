#include "liner.hpp"

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
		std::string filePath;
		ss>>filePath;
		float samplesPerQuarter;
		ss>>samplesPerQuarter;
		getMidi(samplesPerQuarter).write(filePath);
		return "";
	});
	registerCommand("load", "<file path> <samples per quarter>", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		float samplesPerQuarter;
		ss>>samplesPerQuarter;
		dlal::Midi midi;
		midi.read(filePath);
		return putMidi(midi, samplesPerQuarter);
	});
	registerCommand("clear", "", [this](std::stringstream& ss){
		_line.clear();
		return "";
	});
	registerCommand("reset_on_midi", "", [this](std::stringstream& ss){
		_resetOnMidi=true;
		return "";
	});
	registerCommand("serialize_liner", "", [this](std::stringstream&){
		auto midi=getMidi(1);
		std::vector<uint8_t> bytes;
		midi.write(bytes);
		std::stringstream ss;
		ss<<bytes;
		return ss.str();
	});
	registerCommand("deserialize_liner", "<serialized>", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		ss>>bytes;
		dlal::Midi midi;
		midi.read(bytes);
		return putMidi(midi, 1);
	});
}

void Liner::evaluate(){
	advance(_phase);
	if(phase()){
		advance(_period);
		_iterator=_line.begin();
	}
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

void Liner::advance(uint64_t phase){
	while(_iterator&&_iterator->sample<=phase){
		for(auto output: _outputs){
			std::vector<uint8_t>& m=_iterator->midi;
			output->midi(m.data(), m.size());
			_system->_reportQueue.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(output));
		}
		++_iterator;
	}
}

void Liner::put(const uint8_t* midi, unsigned size, uint64_t sample){
	Midi m{sample, std::vector<uint8_t>(midi, midi+size)};
	auto i=_line.begin();
	for(/*nothing*/; i!=_line.end(); ++i) if(i->sample>=sample) break;
	_line.insert(i, m);
	if(!_iterator) setPhase(_phase);
}

Midi Liner::getMidi(float samplesPerQuarter) const {
	dlal::Midi result;
	uint64_t last=0;
	for(auto i: _line){
		auto delta=uint32_t((i.sample-last)/samplesPerQuarter*result.ticksPerQuarter);
		result.append(1, delta, i.midi);
		last=i.sample;
	}
	return result;
}

std::string Liner::putMidi(dlal::Midi midi, float samplesPerQuarter){
	int ticks=0;
	if(midi.tracks.size()<2) return "error: no track to read";
	for(auto i: midi.tracks[0]){
		if(i.type==dlal::Midi::Event::TEMPO) samplesPerQuarter=1.0f*_sampleRate*i.usPerQuarter/1e6;
		if(i.ticks) break;
	}
	auto pairs=getPairs(midi.tracks[1]);
	_line.clear();
	for(auto i: pairs){
		ticks+=i.delta;
		_line.push_back(Midi{uint64_t(ticks*samplesPerQuarter/midi.ticksPerQuarter), i.event});
	}
	resize(midi.duration()*samplesPerQuarter/midi.ticksPerQuarter);
	return "";
}

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Liner::Midi& midi){
	return o<<"{"<<midi.sample<<", "<<midi.midi<<"}";
}
