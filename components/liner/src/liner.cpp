#include "liner.hpp"

#include <obvious.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(Liner)

namespace dlal{

Liner::Liner(){
	_period=44100*8;
	_index=0;
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
		dans::Midi midi;
		midi.read(filePath);
		return putMidi(midi, samplesPerQuarter, track);
	});
	registerCommand("clear", "", [this](std::stringstream& ss){
		_line.clear();
		_index=0;
		return "";
	});
	registerCommand("reset_on_midi", "", [this](std::stringstream& ss){
		_resetOnMidi=true;
		return "";
	});
	registerCommand("transplant_on_midi", "[enable, default 1] [anchor note, default lowest in line]", [this](std::stringstream& ss){
		int enable=1;
		ss>>enable;
		_transplantOnMidi=(bool)enable;
		if(_transplantOnMidi){
			auto i=_line.begin();
			_minNote=0xff;
			_allNotes.clear();
			while(i!=_line.end()){
				const auto& m=i->midi;
				if(m.size()==3&&(m[0]>>4)==9){
					_allNotes.insert(m[1]);
					if(m[1]<_minNote) _minNote=m[1];
				}
				++i;
			}
			int anchorNote;
			if(ss>>anchorNote) _minNote=(uint8_t)anchorNote;
		}
		return "";
	});
	registerCommand("serialize_liner", "", [this](std::stringstream&){
		auto midi=getMidi();
		std::vector<uint8_t> bytes;
		midi.write(bytes);
		std::stringstream ss;
		ss<<::str(_sampleRate, bytes, _samplesPerQuarter, _transplantOnMidi);
		if(_transplantOnMidi){
			ss<<" ";
			ss<<::str(_allNotes, _minNote);
		}
		return ss.str();
	});
	registerCommand("deserialize_liner", "<serialized>", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		::dstr(ss, _sampleRate, bytes, _samplesPerQuarter, _transplantOnMidi);
		if(_transplantOnMidi){
			::dstr(ss, " ");
			::dstr(ss, _allNotes, _minNote);
		}
		dans::Midi midi;
		midi.read(bytes);
		return putMidi(midi, _samplesPerQuarter);
	});
	registerCommand("loop_on_repeat", "[enable, default 1]", [this](std::stringstream& ss){
		int enable=1;
		ss>>enable;
		_loopOnRepeat=(bool)enable;
		return "";
	});
	registerCommand("set_fudge", "<loop-on-repeat fudge in seconds>", [this](std::stringstream& ss){
		ss>>_fudge;
		return "";
	});
}

void Liner::evaluate(){
	if(_transplantOnMidi&&_transplantNote==NOTE_SENTINEL) return;
	advance(_phase);
	if(phase()){
		advance(_period);
		if(_loopOnRepeat){
			if(_genes[0][0].notes.size()&&_genes[0]==_genes[1]){
				//translate _genes[1] into _line
				for(const auto& gene: _genes[1])
					for(const auto& midi: gene.midi)
						put(midi);
			}
			_genes[1]=_genes[0];
			resetGene0();
			if(_genes[1].back().lastNoteOnComparedTo(_period, _sampleRate*_fudge)==Gene::GT){
				_genes[0][0]=_genes[1].back();
				_genes[1].pop_back();
				for(auto& i: _genes[0][0].midi) i.sample=0;
			}
		}
		_index=0;
		if(_transplantOnMidi) _transplantNote=NOTE_SENTINEL;
	}
}

void Liner::midi(const uint8_t* bytes, unsigned size){
	auto stop=[this](){
		for(const auto& note: _allNotes)
			for(auto output: _outputs){
				std::vector<uint8_t> m{0x80, uint8_t(note-_minNote+_transplantNote), 0x40};
				midiSend(output, m.data(), m.size());
			}
		_transplantNote=NOTE_SENTINEL;
	};
	if(_transplantOnMidi){
		if(size==3) switch(bytes[0]>>4){
			case 9:
				stop();
				Periodic::setPhase(0);
				_index=0;
				_transplantNote=bytes[1];
				break;
			case 8: stop(); break;
			default: break;
		}
		return;
	}
	if(_resetOnMidi){
		Periodic::setPhase(0);
		_index=0;
		_resetOnMidi=false;
	}
	process(bytes, size, _phase);
}

std::string Liner::setPhase(uint64_t phase){
	Periodic::setPhase(phase);
	_index=0;
	while(_index<_line.size()&&_line[_index].sample<_phase) ++_index;
	return "";
}

void Liner::advance(uint64_t phase){
	while(_index<_line.size()&&_line[_index].sample<=phase){
		for(auto output: _outputs){
			std::vector<uint8_t>& m=_line[_index].midi;
			uint8_t command=m[0]>>4;
			if(_transplantOnMidi&&(command==9||command==8)){
				uint8_t t[]={m[0], uint8_t(m[1]-_minNote+_transplantNote), m[2]};
				midiSend(output, t, 3);
			}
			else midiSend(output, m.data(), m.size());
		}
		++_index;
	}
}

void Liner::process(const uint8_t* midi, unsigned size, uint64_t sample){
	if(_loopOnRepeat){ if(size){
		//record notes
		auto& g=_genes[0];
		if(midi[0]>>4==9&&midi[2]){
			if(g.back().lastNoteOnComparedTo(sample, _sampleRate*_fudge)==Gene::LT)//new gene
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
	_index=0;
	while(_line[_index].sample<_phase) ++_index;
}

dans::Midi Liner::getMidi() const {
	dans::Midi result;
	result.append(0, 0, dans::Midi::Event().setTempo(int(_samplesPerQuarter*1e6/_sampleRate)));
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

std::string Liner::putMidi(dans::Midi midi, float samplesPerQuarter, unsigned track){
	int ticks=0;
	if(midi.tracks.size()<=track) return "error: no track "+std::to_string(track);
	for(auto i: midi.tracks[0]){
		if(i.type==dans::Midi::Event::TEMPO) samplesPerQuarter=1.0f*_sampleRate*i.usPerQuarter/1e6;
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
	_index=0;
	while(_line[_index].sample<_phase) ++_index;
	return "";
}

void Liner::resetGene0(){
	_genes[0].clear();
	_genes[0].push_back(Gene());//placeholder gene
}

}//namespace dlal
