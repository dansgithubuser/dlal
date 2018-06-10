#include "liner.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Liner)

namespace dlal{

Liner::Liner(): _resetOnMidi(false) {
	_period=44100*8;
	_iterator=_line.begin();
	_checkMidi=true;
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
	registerCommand("save", "<file path>", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		getMidi().write(filePath);
		return "";
	});
	registerCommand("load", "<file path> [<samples per quarter>]", [this](std::stringstream& ss){
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
		auto midi=getMidi();
		std::vector<uint8_t> bytes;
		midi.write(bytes);
		std::stringstream ss;
		ss<<_sampleRate<<" "<<bytes<<" "<<_samplesPerQuarter;
		return ss.str();
	});
	registerCommand("deserialize_liner", "<serialized>", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		ss>>_sampleRate>>" ">>bytes>>" ">>_samplesPerQuarter;
		dlal::Midi midi;
		midi.read(bytes);
		return putMidi(midi, _samplesPerQuarter);
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
			midiSend(output, m.data(), m.size());
		}
		++_iterator;
	}
}

void Liner::put(const uint8_t* midi, unsigned size, uint64_t sample){
	Midi m(sample, std::vector<uint8_t>(midi, midi+size));
	auto i=_line.begin();
	for(/*nothing*/; i!=_line.end(); ++i) if(i->sample>=sample) break;
	_line.insert(i, m);
	if(!_iterator) setPhase(_phase);
}

Midi Liner::getMidi() const {
	dlal::Midi result;
	result.append(0, 0, dlal::Midi::Event().setTempo(int(_samplesPerQuarter*1e6/_sampleRate)));
	uint64_t last=0;
	float lastRemainder=0.0f;
	for(auto i: _line){
		auto delta=uint32_t((i.sample+i.sampleRemainder-last-lastRemainder)/_samplesPerQuarter*result.ticksPerQuarter+0.5f);
		result.append(1, delta, i.midi);
		last=i.sample;
		lastRemainder=i.sampleRemainder;
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
	_samplesPerQuarter=samplesPerQuarter;
	auto pairs=getPairs(midi.tracks[1]);
	_line.clear();
	float latestSample=0.0f;
	for(auto i: pairs){
		ticks+=i.delta;
		auto sample=ticks*samplesPerQuarter/midi.ticksPerQuarter;
		auto sampleI=uint64_t(sample);
		_line.push_back(Midi(sampleI, sample-sampleI, i.event));
		if(sample>latestSample) latestSample=sample;
	}
	resize(latestSample);
	setPhase(_phase);
	return "";
}

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Liner::Midi& midi){
	return o<<"{"<<midi.sample<<", "<<midi.midi<<"}";
}
