#include "liner.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Liner; }

namespace dlal{

Liner::Liner(): _sample(0), _period(0), _index(0) {
	_checkMidi=true;
	addJoinAction([this](System&){
		if(!_period) return "error: size not set";
		return "";
	});
	registerCommand("resize", "<period in samples>", [this](std::stringstream& ss){
		ss>>_period;
		return "";
	});
	registerCommand("crop", "", [this](std::stringstream& ss){
		_period=_sample;
		_sample=0;
		_index=0;
		return "";
	});
	registerCommand("reset", "", [this](std::stringstream& ss){
		_sample=0;
		_index=0;
		return "";
	});
	registerCommand("midi", "<time in samples> byte[1]..byte[n]",
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
}

void Liner::evaluate(){
	//output
	while(_index<_line.size()&&_line[_index].sample<=_sample){
		for(auto output: _outputs){
			std::vector<uint8_t>& m=_line[_index].midi;
			output->midi(m.data(), m.size());
			_system->_reportQueue.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(output));
		}
		++_index;
	}
	//move forward
	_sample+=_samplesPerEvaluation;
	if(_sample>=_period){
		_sample-=_period;
		_index=0;
	}
}

void Liner::midi(const uint8_t* bytes, unsigned size){
	put(bytes, size, _sample);
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
