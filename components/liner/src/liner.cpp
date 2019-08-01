#include "liner.hpp"

#include <cmath>
#include <exception>

#include <obvious.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(Liner)

namespace dlal{

std::string Liner::Midi::str() const {
	return ::str(sample, midi);
}

Liner::Liner(){
	_period=44100*8;
	_index=0;
	_checkMidi=true;
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
	registerCommand("load", "<file path> [resize] [track]", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		int doResize=1;
		ss>>doResize;
		unsigned track=1;
		ss>>track;
		dans::Midi midi;
		try{ midi.read(filePath); }
		catch(std::exception& e){ return ::str("error:", e.what()); }
		return putMidi(midi, doResize, track);
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
	registerCommand("get_midi", "", [this](std::stringstream&){
		auto midi=getMidi();
		std::vector<uint8_t> bytes;
		midi.write(bytes);
		return ::str(bytes);
	});
	registerCommand("put_midi", "bytes", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		unsigned u;
		while(ss>>u) bytes.push_back(u);
		dans::Midi midi;
		midi.read(bytes);
		return putMidi(midi, false);
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
		return putMidi(midi);
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
	registerCommand("samples_per_quarter", "[samples]", [this](std::stringstream& ss){
		ss>>_samplesPerQuarter;
		return ::str(_samplesPerQuarter);
	});
}

std::string Liner::disconnect(Component& output){
	for(uint8_t i=0; i<=127; ++i)
		for(auto output: _outputs)
			midiSend(output, std::vector<uint8_t>{0x80, i, 0x40}.data(), 3);
	MultiOut::disconnect(output);
	return "";
}

void Liner::evaluate(){
	if(_transplantOnMidi&&_transplantNote==NOTE_SENTINEL) return;
	advance(_phase);
	if(phase()){
		advance(_period);
		if(_loopOnRepeat){
			bool equal=false;
			std::vector<Midi>::iterator i0=_genes[0].begin();
			std::vector<Midi>::iterator i1=_genes[1].begin();
			while(true){
				auto g1=grabGene(i0, _genes[0].end());
				auto g2=grabGene(i1, _genes[1].end());
				if(i0==_genes[0].end()&&i1==_genes[1].end()) break;
				equal=g1==g2;
				if(!equal) break;
			}
			if(equal){
				//translate _genes[1] into _line
				std::set<uint8_t> notes;
				for(const auto& midi: _genes[0]){
					put(midi);
					const auto& m=midi.midi;
					if(m.size()==3){
						if(m[0]>>4==9){
							if(m[2])
								notes.insert(m[1]);
							else
								notes.erase(m[1]);
						}
						else if(m[0]>>4==8)
							notes.erase(m[1]);
					}
				}
				for(const auto& i: notes){
					put(Midi(_period, std::vector<uint8_t>{0x80, i, 0}));
				}
			}
			_genes[1]=_genes[0];
			_genes[0].clear();
			for(auto i=_genes[1].rbegin(); i!=_genes[1].rend(); ++i){
				if(i->sample+_fudge*_sampleRate<_period){//find something that should stay in gene1
					//move note ons strictly ahead to gene0
					for(auto j=i.base(); j!=_genes[1].end(); ++j){
						if(j->midi[0]>>4==9&&j->midi[2]){
							_genes[0].push_back(*j);
							_genes[0].back().sample-=_period;
							j->midi=std::vector<uint8_t>{0xff, 1, 0};//empty text event
						}
					}
					break;
				}
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
	while(_index<_line.size()&&(_line[_index].sample<=phase||phase==_period)){
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
		//record midi
		_genes[0].push_back(Midi(
			sample, std::vector<uint8_t>(midi, midi+size)
		));
	}}
	else put(Midi(sample, std::vector<uint8_t>(midi, midi+size)));
}

void Liner::put(Midi m){
	if(!m.midi.size()) return;
	if(m.midi[0]==0xff) return;
	if(m.sample<0) m.sample=0;
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

std::string Liner::putMidi(dans::Midi midi, bool doResize, unsigned track){
	int ticks=0;
	if(midi.tracks.size()<=track) return "error: no track "+std::to_string(track);
	auto pairs=getPairs(midi.tracks[track]);
	_line.clear();
	float latestSample=0.0f;
	for(auto i: pairs){
		ticks+=i.delta;
		auto sample=ticks*_samplesPerQuarter/midi.ticksPerQuarter;
		auto sampleI=uint64_t(sample);
		_line.push_back(Midi(sampleI, sample-sampleI, i.event));
		if(sample>latestSample) latestSample=sample;
	}
	if(doResize) resize(latestSample);
	setPhase(_phase);
	if(!_line.size()) return "";
	_index=0;
	while(_line[_index].sample<_phase) ++_index;
	return "";
}

std::set<uint8_t> Liner::grabGene(std::vector<Liner::Midi>::iterator& i, std::vector<Liner::Midi>::iterator end) const {
	std::set<uint8_t> result;
	int64_t ni, nf;
	//find the next note
	while(i!=end){
		if(i->midi[0]>>4==9&&i->midi[2]){
			result.insert(i->midi[1]);
			ni=i->sample;
			nf=noteEnd(i, end);
			++i;
			break;
		}
		++i;
	}
	//find notes that overlap the original note
	auto j=i;
	while(j!=end){
		if(j->midi[0]>>4==9&&j->midi[2]){
			int64_t
				mi=j->sample,
				mf=noteEnd(j, end);
			if(4*std::abs((nf+ni)-(mf+mi))>nf-ni+mf-mi)//distance between midpoints vs combined length
				break;//not overlapping
			result.insert(j->midi[1]);
			i=j+1;
		}
		++j;
	}
	return result;
};

int64_t Liner::noteEnd(std::vector<Midi>::iterator i, std::vector<Midi>::iterator end) const {
	uint8_t note=i->midi[1];
	while(++i!=end) if(
		(i->midi[0]>>4==8||i->midi[0]>>4==9&&!i->midi[2])
		&&
		i->midi[1]==note
	) return i->sample;
	return _period;
}

}//namespace dlal
