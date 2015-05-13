#include "liner.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Liner; }

namespace dlal{

Liner::Liner(): _midi(&_emptyMidi), _sample(0), _period(0) {
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
			_line[sample].push_back(message);
			return "";
		}
	);
}

std::string Liner::addInput(Component* input){
	if(!input->readMidi()) return "error: input must provide midi!";
	_inputs.push_back(input);
	return "";
}

std::string Liner::readyToEvaluate(){
	if(!_period) return "error: period not set";
	return "";
}

void Liner::evaluate(unsigned samples){
	//record inputs
	for(auto input: _inputs){
		MidiMessages& midi=*input->readMidi();
		if(midi.size()) _line[_sample].push_back(midi);
	}
	//set output
	_midi=&_emptyMidi;
	if(_line.count(_sample)) _midi=&_line[_sample];
	//move forward
	_sample+=samples;
	_sample%=_period;
}

MidiMessages* Liner::readMidi(){ return _midi; }

}//namespace dlal
