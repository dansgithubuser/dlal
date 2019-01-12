#include "liner.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Liner)

static const unsigned FUDGE_PER_SECOND=20;

namespace dlal{

Liner::Liner(){
	_period=44100*8;
	_iterator=_line.begin();
	_checkMidi=true;
	resetGene0();
	registerCommand("midi_event", "<time in samples> byte[1]..byte[n]",
		[this](std::stringstream& ss){
			unsigned sample;
			ss>>sample;
			std::vector<uint8_t> m;
			unsigned byte;
			while(ss>>byte) m.push_back(byte);
			process(m.data(), m.size(), sample);
			return "";
		}
	);
	registerCommand("save", "<file path>", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		getMidi().write(filePath);
		return "";
	});
	registerCommand("load", "<file path> [<samples per quarter>] [track]", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		float samplesPerQuarter=22050.0f;
		ss>>samplesPerQuarter;
		unsigned track=1;
		ss>>track;
		dlal::Midi midi;
		midi.read(filePath);
		return putMidi(midi, samplesPerQuarter, track);
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
	registerCommand("loop_on_repeat", "<enable>", [this](std::stringstream& ss){
		int enable=1;
		ss>>enable;
		_loopOnRepeat=(bool)enable;
		return "";
	});
}

void Liner::evaluate(){
	advance(_phase);
	if(phase()){
		advance(_period);
		if(_loopOnRepeat){
			if(_genes[0][0].midi.size()&&_genes[0]==_genes[1]){
				//translate _genes[1] into _line
				for(const auto& gene: _genes[1])
					for(const auto& midi: gene.midi)
						put(midi);
			}
			_genes[1]=_genes[0];
			resetGene0();
			if(_genes[1].back().lastNoteOnComparedTo(_period, _sampleRate/FUDGE_PER_SECOND)==Gene::GT){
				_genes[0][0]=_genes[1].back();
				_genes[1].pop_back();
				for(auto& i: _genes[0][0].midi) i.sample=0;
			}
		}
		_iterator=_line.begin();
	}
}

void Liner::midi(const uint8_t* bytes, unsigned size){
	if(_resetOnMidi){
		_phase=0;
		_iterator=_line.begin();
		_resetOnMidi=false;
	}
	process(bytes, size, _phase);
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

void Liner::process(const uint8_t* midi, unsigned size, uint64_t sample){
	if(_loopOnRepeat){ if(size){
		//record notes
		auto& g=_genes[0];
		if(midi[0]>>4==9&&midi[2]){
			if(g.back().lastNoteOnComparedTo(sample, _sampleRate/FUDGE_PER_SECOND)==Gene::LT)//new gene
				if(g.size()!=1||g[0].notes.size()) g.push_back(Gene());//no placeholder gene
			g.back().notes.insert(midi[1]);//put the note in the gene
		}
		//record midi
		g.back().midi.push_back(Midi(
			sample, std::vector<uint8_t>(midi, midi+size)
		));
	}}
	else put(Midi(sample, std::vector<uint8_t>(midi, midi+size)));
}

void Liner::put(const Midi& m){
	auto i=_line.begin();
	for(/*nothing*/; i!=_line.end(); ++i) if(i->sample>=m.sample) break;
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

std::string Liner::putMidi(dlal::Midi midi, float samplesPerQuarter, unsigned track){
	int ticks=0;
	if(midi.tracks.size()<=track) return "error: no track "+std::to_string(track);
	for(auto i: midi.tracks[0]){
		if(i.type==dlal::Midi::Event::TEMPO) samplesPerQuarter=1.0f*_sampleRate*i.usPerQuarter/1e6;
		if(i.ticks) break;
	}
	_samplesPerQuarter=samplesPerQuarter;
	auto pairs=getPairs(midi.tracks[track]);
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

void Liner::resetGene0(){
	_genes[0].clear();
	_genes[0].push_back(Gene());//placeholder gene
}

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Liner::Midi& midi){
	return o<<"{"<<midi.sample<<", "<<midi.midi<<"}";
}
