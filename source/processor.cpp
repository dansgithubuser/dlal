#include "processor.hpp"

#include <sstream>

namespace dlal{

Processor::Processor(unsigned sampleRate, unsigned size, std::ostream& errorStream):
	_errorStream(errorStream),
	_sampleRate(sampleRate),
	_samples(size, 0.0f),
	_queue(128)
{
	Op op;
	op.mic.resize(size);
	_queue.setAll(op);
}

void Processor::addObject(const std::string& name, Object object, int channel){
	_objects[name]=object;
	_queue.write()->type=Op::ACTIVATE;
	_queue.write()->object=&_objects[name];
	_queue.nextWrite();
}

void Processor::processText(const std::string& line){
	std::stringstream ss(line);
	std::string s;
	ss>>s;
	if(s=="sonic"){
		std::string name;
		unsigned channel;
		if(!(ss>>name)||!(ss>>channel))
			_errorStream<<"Must specify name and channel of sonic."<<std::endl;
		Sonic sonic(_samples.data(), _sampleRate);
		_objects[name].type=Object::SONIC;
		_objects[name].sonic=sonic;
		_queue.write()->type=Op::ACTIVATE;
		_queue.write()->object=&_objects[name];
		_queue.write()->channel=channel;
		_queue.nextWrite();
	}
	else{
		std::vector<unsigned char> midi;
		midi.push_back(0x90);
		midi.push_back(60);
		midi.push_back(64);
		_queue.write()->type=Op::MIDI;
		_queue.write()->midi=midi;
		_queue.nextWrite();
	}
}

void Processor::processMidi(const std::vector<unsigned char>& midi){
	_queue.write()->type=Op::MIDI;
	_queue.write()->midi=midi;
	_queue.nextWrite();
}

void Processor::processMic(const float* samples){
	_queue.write()->type=Op::MIC;
	_queue.write()->mic.resize(_samples.size());
	for(unsigned i=0; i<_samples.size(); ++i) _queue.write()->mic[i]=samples[i];
	_queue.nextWrite();
}

void Processor::output(float* samples){
	for(unsigned i=0; i<_samples.size(); ++i) _samples[i]=0.0f;
	while(_queue.read()){
		processOp(*_queue.read());
		_queue.nextRead();
	}
	for(auto i: _channelToObject){
		switch(i.second->type){
			case Object::SONIC:
				i.second->sonic.evaluate(_samples.size());
				break;
			default: break;
		}
	}
	for(unsigned i=0; i<_samples.size(); ++i) samples[i]=_samples[i];
}

void Processor::processOp(const Op& op){
	switch(op.type){
		case Op::MIDI:{
			unsigned channel=op.midi[0]&0x0f;
			if(!_channelToObject.count(channel)) break;
			_channelToObject[channel]->sonic.processMidi(op.midi);
			break;
		}
		case Op::MIC:
			for(unsigned i=0; i<_samples.size(); ++i) _samples[i]+=op.mic[i];
			break;
		case Op::ACTIVATE:
			_channelToObject[op.channel]=op.object;
			break;
		default: break;
	}
}

}//namespace dlal
