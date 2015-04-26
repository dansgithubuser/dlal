#include "liner.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Liner; }

namespace dlal{

Liner::Liner(): _sample(0), _index(0), _period(0) {
	registerCommand("period", "<period in samples>", [&](std::stringstream& ss){
		ss>>_period;
		return "";
	});
	registerCommand("midi", "<time in samples> byte[1]..byte[n]",
		[&](std::stringstream& ss){
			unsigned sample;
			ss>>sample;
			MidiMessage message;
			unsigned byte, i=0;
			while(ss>>std::hex>>byte&&i<MidiMessage::SIZE){
				message._bytes[i]=byte;
				++i;
			}
			for(i=0; i<_line.size(); ++i){
				if(_line[i]._sample>sample) break;
				if(_line[i]._sample==sample){
					_line[i]._midi.push_back(message);
					return "";
				}
			}
			_line.insert(_line.begin()+i, TimedMidi{ sample, message });
			return "";
		}
	);
}

std::string Liner::readyToEvaluate(){
	if(!_period) return "error: period not set";
	return "";
}

void Liner::evaluate(unsigned samples){
	_sample+=samples;
	if(_sample>_period){
		_sample-=_period;
		_index=0;
	}
	_midi.clear();
	while(_line[_index]._sample<_sample){
		_midi.push_back(_line[_index]._midi);
		++_index;
	}
}

MidiMessages* Liner::readMidi(){ return &_midi; }

}//namespace dlal
