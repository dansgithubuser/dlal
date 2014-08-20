#include "processor.hpp"

#include <sstream>

namespace dlal{

Processor::Processor(unsigned sampleRate, unsigned size, std::ostream& errorStream):
	_errorStream(errorStream),
	_sampleRate(sampleRate),
	_samples(size, 0.0f),
	_queue(128),
	_beat(0),
	_samplesAfterBeat(0),
	_samplesPerBeat(0),
	_beatsPerLoop(0),
	_nextSamplesPerBeat(0),
	_nextBeatsPerLoop(0)
{
	Op op;
	op.mic.resize(size);
	_queue.setAll(op);
}

void Processor::addSonic(const std::string& name, Sonic sonic, int channel){
	_sonics[name]=sonic;
	_queue.write()->type=Op::SONIC;
	_queue.write()->sonic=&_sonics[name];
	_queue.nextWrite();
}

void Processor::processText(const std::string& line){
	std::stringstream ss(line);
	std::string s;
	ss>>s;
	if(s=="sonic"){
		std::string name;
		int channel;
		if(!(ss>>name)||!(ss>>channel))
			_errorStream<<"Must specify name and channel of sonic."<<std::endl;
		Sonic sonic(_samples.data(), _sampleRate);
		_sonics[name]=sonic;
		_queue.write()->type=Op::SONIC;
		_queue.write()->sonic=&_sonics[name];
		_queue.write()->channel=channel;
		_queue.nextWrite();
	}
	else if(s=="tempo"){
		unsigned tempo;
		ss>>tempo;
		_queue.write()->type=Op::TEMPO;
		_queue.write()->samplesPerBeat=_sampleRate*60/tempo;
		_queue.nextWrite();
	}
	else if(s=="length"){
		unsigned beatsPerLoop;
		ss>>beatsPerLoop;
		_queue.write()->type=Op::LENGTH;
		_queue.write()->beatsPerLoop=beatsPerLoop;
		_queue.nextWrite();
	}
	else if(s=="line"){
		std::string name;
		int channel;
		if(!(ss>>name)||!(ss>>channel)){
			_errorStream<<"Must specify name and channel of line."<<std::endl;
			return;
		}
		if(channel<0||channel>=16){
			_errorStream<<"Channel must be between 0 and 15."<<std::endl;
			return;
		}
		Line line;
		Line::Event event;
		event.beat=0.0f;
		event.message.push_back(channel);
		event.message.push_back(0);
		event.message.push_back(64);
		float stride=1.0f;
		float duty=0.99f;
		int octave=5;
		while(ss>>s){
			if(s=="o"){
				int o;
				ss>>o;
				octave+=o;
				if(octave<0){
					octave=0;
					_errorStream<<"Ignoring too-low octave change."<<std::endl;
				}
				else if(octave>15){
					octave=15;
					_errorStream<<"Ignoring too-high octave change."<<std::endl;
				}
			}
			else if(s=="t"){
				ss>>stride;
			}
			else if(s.size()==1){
				if(s=="."){
					event.beat+=stride;
					continue;
				}
				int note=-1;
				switch(s[0]){
					case 'z': note=0; break;
					case 's': note=1; break;
					case 'x': note=2; break;
					case 'd': note=3; break;
					case 'c': note=4; break;
					case 'v': note=5; break;
					case 'g': note=6; break;
					case 'b': note=7; break;
					case 'h': note=8; break;
					case 'n': note=9; break;
					case 'j': note=10; break;
					case 'm': note=11; break;
					default:
						_errorStream<<"Ignoring invalid token "<<s<<"."<<std::endl;
						break;
				}
				if(note>=0){
					//note on
					event.message[0]&=0x0f;
					event.message[0]|=0x90;
					//note number
					event.message[1]=12*octave+note;
					//note on line event
					line.events.push_back(event);
					//note off line event
					event.beat+=stride*duty;
					event.message[0]&=0x0f;
					event.message[0]|=0x80;
					line.events.push_back(event);
					//next note start time
					event.beat+=stride*(1-duty);
				}
			}
			else _errorStream<<"Ignoring invalid token "<<s<<"."<<std::endl;
		}
		_lines[name]=line;
	}
	else if(s=="activateLine"){
		ss>>s;
		if(!_lines.count(s)){
			_errorStream<<"Line "<<s<<" does not exist."<<std::endl;
			return;
		}
		_queue.write()->type=Op::LINE;
		_queue.write()->line=&_lines[s];
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
	//update beat
	if(_samplesPerBeat&&_beatsPerLoop){
		_samplesAfterBeat+=_samples.size();
		if(_samplesAfterBeat>=_samplesPerBeat){
			_samplesAfterBeat-=_samplesPerBeat;
			++_beat;
			if(_beat>=_beatsPerLoop){
				_beat-=_beatsPerLoop;
				//update length
				if(_nextBeatsPerLoop){
					_beatsPerLoop=_nextBeatsPerLoop;
					_nextBeatsPerLoop=0;
				}
				//update tempo
				if(_nextSamplesPerBeat){
					_samplesPerBeat=_nextSamplesPerBeat;
					_nextSamplesPerBeat=0;
				}
				//update lines
				for(auto line: _nextLines) _activeLines.push_back(line);
				_nextLines.clear();
				//reset lines
				for(auto line: _activeLines) line->i=0;
			}
		}
	}
	//lines
	float beat=_beat+1.0f*_samplesAfterBeat/_samplesPerBeat;
	for(auto line: _activeLines){
		while(line->i<line->events.size()&&beat>=line->events[line->i].beat){
			Op op;
			op.type=Op::MIDI;
			op.midi=line->events[line->i].message;
			processOp(op);
			++line->i;
		}
	}
	//reset sample
	for(unsigned i=0; i<_samples.size(); ++i) _samples[i]=0.0f;
	//process ops
	while(_queue.read()){
		processOp(*_queue.read());
		_queue.nextRead();
	}
	//process sonics
	for(auto i: _channelToSonic) i.second->evaluate(_samples.size());
	//copy from working buffer to output buffer
	for(unsigned i=0; i<_samples.size(); ++i) samples[i]=_samples[i];
}

Processor::Line::Line(): i(0) {}

void Processor::processOp(const Op& op){
	switch(op.type){
		case Op::MIDI:{
			unsigned channel=op.midi[0]&0x0f;
			if(!_channelToSonic.count(channel)) break;
			_channelToSonic[channel]->processMidi(op.midi);
			break;
		}
		case Op::MIC:
			for(unsigned i=0; i<_samples.size(); ++i) _samples[i]+=op.mic[i];
			break;
		case Op::SONIC:
			_channelToSonic[op.channel]=op.sonic;
			break;
		case Op::TEMPO:
			if(_samplesPerBeat) _nextSamplesPerBeat=op.samplesPerBeat;
			else _samplesPerBeat=op.samplesPerBeat;
			break;
		case Op::LENGTH:
			if(_beatsPerLoop) _nextBeatsPerLoop=op.beatsPerLoop;
			else _beatsPerLoop=op.beatsPerLoop;
			break;
		case Op::LINE:
			_nextLines.push_back(op.line);
			break;
		default: break;
	}
}

}//namespace dlal
