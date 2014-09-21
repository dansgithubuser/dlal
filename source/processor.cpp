#include "processor.hpp"

#include <sstream>
#include <thread>
#include <chrono>

namespace dlal{

Processor::Processor(unsigned sampleRate, unsigned size, std::ostream& errorStream):
	_errorStream(errorStream),
	_sampleRate(sampleRate),
	_samples(size, 0.0f),
	_queue(8),
	_beat(0),
	_samplesAfterBeat(0),
	_samplesPerBeat(0),
	_beatsPerLoop(0),
	_nextSamplesPerBeat(0),
	_nextBeatsPerLoop(0),
	_reqdSamplesPerBeat(0),
	_reqdBeatsPerLoop(0),
	_lastBeat(0),
	_currentRec(0),
	_currentRecPair(0),
	_switchRecPair(false),
	_recSample(0)
{
	Op op;
	op.mic.resize(size);
	_queue.setAll(op);
	_mic.resize(1);
	_mic[0].resize(size);
	if(!_queue.lockless()) errorStream<<"Warning: queue is not lockless.\n";
}

void Processor::processText(const std::string& line){
	std::stringstream ss(line);
	std::string s;
	while(ss>>s){
		if(s=="sonic"){
			std::string name;
			int channel;
			if(!(ss>>name)||!(ss>>channel)){
				_errorStream<<"Must specify name and channel of sonic."<<std::endl;
				continue;
			}
			Sonic sonic(_samples.data(), _sampleRate);
			_sonics[name]=sonic;
			_queue.write(Op(&_sonics[name], channel));
		}
		else if(s=="sonicConnect"){
			if(!(ss>>s)){
				_errorStream<<"Must specify name of sonic."<<std::endl;
				continue;
			}
			if(!_sonics.count(s)){
				_errorStream<<"Sonic "<<s<<" does not exist."<<std::endl;
				continue;
			}
			unsigned i, j;
			if(!(ss>>i)){
				_errorStream<<"Must specify source oscillator."<<std::endl;
				continue;
			}
			if(!(ss>>j)){
				_errorStream<<"Must specify destination oscillator."<<std::endl;
				continue;
			}
			if(i>=Sonic::OSCILLATORS||j>=Sonic::OSCILLATORS){
				_errorStream<<"Oscillator must be between 0 and "<<Sonic::OSCILLATORS<<"."<<std::endl;
				continue;
			}
			float amount;
			if(!(ss>>amount)){
				_errorStream<<"Must specify modulation amount."<<std::endl;
				continue;
			}
			if(amount<0.0f||amount>1.0f){
				_errorStream<<"Amount must be between 0 and 1."<<std::endl;
				continue;
			}
			_sonics[s].oscillators[j]._inputs[i]=amount;
		}
		else if(s=="sonicAdsr"){
			if(!(ss>>s)){
				_errorStream<<"Must specify name of sonic."<<std::endl;
				continue;
			}
			if(!_sonics.count(s)){
				_errorStream<<"Sonic "<<s<<" does not exist."<<std::endl;
				continue;
			}
			unsigned i;
			if(!(ss>>i)){
				_errorStream<<"Must specify source oscillator."<<std::endl;
				continue;
			}
			if(i>=Sonic::OSCILLATORS){
				_errorStream<<"Oscillator must be between 0 and "<<Sonic::OSCILLATORS<<"."<<std::endl;
				continue;
			}
			float att, dec, sus, rel;
			if(!(ss>>att)||!(ss>>dec)||!(ss>>sus)||!(ss>>rel)){
				_errorStream<<"Must specify attack, decay, sustain, and release."<<std::endl;
				continue;
			}
			if(att<0||dec<0||dec>1||sus<0||rel<0){
				_errorStream<<"Attack, decay, sustain, and release must be positive. Decay must be less than 1."<<std::endl;
				continue;
			}
			_sonics[s].oscillators[i]._attack=att;
			_sonics[s].oscillators[i]._decay=dec;
			_sonics[s].oscillators[i]._sustain=sus;
			_sonics[s].oscillators[i]._release=rel;
		}
		else if(s=="wait"){
			float duration;
			ss>>duration;
			if(duration<0||duration>1){
				_errorStream<<"Duration must be between 0 and 1."<<std::endl;
				continue;
			}
			std::cout<<"Waiting."<<std::endl;
			std::this_thread::sleep_for(std::chrono::milliseconds(int(1000*duration)));
		}
		else if(s=="tempo"){
			unsigned tempo;
			ss>>tempo;
			_reqdSamplesPerBeat=_sampleRate*60/tempo;
			_queue.write(Op(Op::TEMPO, _reqdSamplesPerBeat));
			allocateNextRecPair(_reqdBeatsPerLoop*_reqdSamplesPerBeat);
			if(tempo>400) _errorStream<<"Tempo will be very high."<<std::endl;
			if(tempo<30) _errorStream<<"Tempo will be very low."<<std::endl;
		}
		else if(s=="length"){
			ss>>_reqdBeatsPerLoop;
			_queue.write(Op(Op::LENGTH, _reqdBeatsPerLoop));
			allocateNextRecPair(_reqdBeatsPerLoop*_reqdSamplesPerBeat);
			if(_reqdBeatsPerLoop>128) _errorStream<<"Length will be very high."<<std::endl;
		}
		else if(s=="line"){
			std::string name;
			int channel;
			if(!(ss>>name)||!(ss>>channel)){
				_errorStream<<"Must specify name and channel of line."<<std::endl;
				continue;
			}
			if(channel<0||channel>=16){
				_errorStream<<"Channel must be between 0 and 15."<<std::endl;
				continue;
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
				if(s=="l"){
					if(!(ss>>s)){
						_errorStream<<"Must specify line name."<<std::endl;
						continue;
					}
					if(!_lines.count(s)){
						_errorStream<<"Line "<<s<<" does not exist."<<std::endl;
						continue;
					}
					unsigned n;
					if(!(ss>>n)){
						_errorStream<<"Must specify multiplicity of line."<<std::endl;
						continue;
					}
					if(n>128){
						_errorStream<<"Multiplicity must be less than 128."<<std::endl;
						continue;
					}
					float lineStride;
					if(!(ss>>lineStride)){
						_errorStream<<"Must specify line stride."<<std::endl;
						continue;
					}
					if(lineStride<_lines[s].events.back().beat||lineStride>128){
						_errorStream<<"Line stride must be between line length and 128."<<std::endl;
						continue;
					}
					for(unsigned i=0; i<n; ++i){
						for(unsigned j=0; j<_lines[s].events.size(); ++j){
							Line::Event e=_lines[s].events[j];
							e.beat+=event.beat;
							line.events.push_back(e);
						}
						event.beat+=lineStride;
					}
				}
				else if(s=="o"){
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
					if(s==","){
						event.beat+=stride;
						continue;
					}
					else if(s==".") break;
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
				continue;
			}
			_queue.write(Op(Op::LINE, &_lines[s]));
		}
		else if(s=="deactivateLine"){
			ss>>s;
			if(!_lines.count(s)){
				_errorStream<<"Line "<<s<<" does not exist."<<std::endl;
				continue;
			}
			_queue.write(Op(Op::UNLINE, &_lines[s]));
		}
		else if(s=="beat"){
			float beat;
			if(!(ss>>beat)){
				_errorStream<<"Must specify beat."<<std::endl;
				continue;
			}
			if(beat<0.0f){
				_errorStream<<"Beat must be greater than 0."<<std::endl;
				continue;
			}
			if(beat>=_beatsPerLoop){
				_errorStream<<"Beat must be less than beats per loop."<<std::endl;
				continue;
			}
			_queue.write(Op(beat));
		}
		else if(s=="silence"){
			_queue.write(Op(Op::SILENCE));
		}
		else if(s=="record"){
			if(!(ss>>s)) _errorStream<<"Must name record."<<std::endl;
			_recs[s].clear();
			_recs[s].reserve(_beatsPerLoop*_samplesPerBeat);
			_queue.write(Op(Op::REC_MAKE, &_recs[s]));
		}
		else if(s=="activateRecord"){
			ss>>s;
			if(!_recs.count(s)){
				_errorStream<<"Record "<<s<<" does not exist."<<std::endl;
				continue;
			}
			_queue.write(Op(Op::REC, &_recs[s]));
		}
		else if(s=="deactivateRecord"){
			ss>>s;
			if(!_recs.count(s)){
				_errorStream<<"Record "<<s<<" does not exist."<<std::endl;
				continue;
			}
			_queue.write(Op(Op::UNREC, &_recs[s]));
		}
		else _errorStream<<"Unknown command "<<s<<std::endl;
		while(ss>>s){
			if(s==";") break;
			_errorStream<<"Ignoring token "<<s<<std::endl;
		}
	}
}

void Processor::processMidi(const std::vector<unsigned char>& midi){
	_queue.write(Op(midi));
}

void Processor::processMic(const float* samples, unsigned size, unsigned micIndex){
	_queue.write(Op(samples, size, micIndex));
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
				processNexts();
				for(auto line: _activeLines) line->i=0;
			}
			_lastBeat=_beat+1;
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
	while(_queue.getRead()){
		processOp(*_queue.getRead());
		_queue.nextRead();
	}
	//process mic
	Rec& rec=_recPairs[_currentRecPair][_currentRec];
	if(rec.capacity){
		unsigned max=std::min(_samples.size(), rec.capacity-rec.size);
		for(unsigned i=0; i<_mic.size(); ++i) rec.push_back(0.0f);
		for(unsigned i=0; i<_mic.size(); ++i)
			for(unsigned j=0; j<max; ++j)
				rec[j]+=_mic[i][j];
	}
	//process sonics
	for(auto i: _channelToSonic) i.second->evaluate(_samples.size());
	//process recordings
	for(auto rec: _activeRecs){
		unsigned recSample=_recSample;
		for(unsigned i=0; i<_samples.size(); ++i){
			if(recSample>=rec->size) break;
			_samples[i]+=(*rec).samples[recSample];
			++recSample;
		}
	}
	_recSample+=_samples.size();
	//copy from working buffer to output buffer
	for(unsigned i=0; i<_samples.size(); ++i) samples[i]=_samples[i];
}

unsigned Processor::beat(){
	unsigned result=_lastBeat;
	_lastBeat=0;
	return result;
}

Processor::Line::Line(): i(0) {}

Processor::Rec::Rec(): samples(NULL), size(0), capacity(0) {}

Processor::Rec::Rec(Rec& other){
	samples=other.samples;
	other.samples=NULL;
	size=other.size;
	capacity=other.capacity;
}

Processor::Rec::~Rec(){
	delete samples;
}

float& Processor::Rec::operator[](unsigned i){ return samples[i]; }
const float& Processor::Rec::operator[](unsigned i) const{ return samples[i]; }

void Processor::Rec::reserve(unsigned newCapacity){
	delete samples;
	samples=new float[newCapacity];
	capacity=newCapacity;
}

bool Processor::Rec::push_back(float f){
	if(size>=capacity) return false;
	samples[size++]=f;
	return true;
}

void Processor::Rec::clear(){
	size=0;
}

Processor::Op::Op(){}

Processor::Op::Op(Type t): type(t) {}

Processor::Op::Op(Type t, unsigned x): type(t) {
	switch(type){
		case TEMPO: samplesPerBeat=x;
		case LENGTH: beatsPerLoop=x;
		default: break;
	}
}

Processor::Op::Op(Type t, Line* l): type(t), line(l) {}

Processor::Op::Op(Type t, Rec* r): type(t), rec(r) {}

Processor::Op::Op(Sonic* sonic, unsigned channel):
	type(SONIC), sonic(sonic), channel(channel)
{}

Processor::Op::Op(float beat): type(BEAT), beat(beat) {}

Processor::Op::Op(const std::vector<unsigned char>& midi):
	type(MIDI), midi(midi)
{}

Processor::Op::Op(const float* samples, unsigned size, unsigned micIndex):
	type(MIC), micIndex(micIndex)
{
	mic.resize(size);
	for(unsigned i=0; i<size; ++i) mic[i]=samples[i];
}

void Processor::processOp(const Op& op){
	switch(op.type){
		case Op::MIDI:{
			unsigned channel=op.midi[0]&0x0f;
			if(!_channelToSonic.count(channel)) break;
			_channelToSonic[channel]->processMidi(op.midi);
			break;
		}
		case Op::MIC:{
			if(_mic.size()<=op.micIndex) _mic.resize(op.micIndex+1);
			_mic[op.micIndex]=op.mic;
			break;
		}
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
		case Op::UNLINE:
			_removeLines.push_back(op.line);
			break;
		case Op::BEAT:
			_beat=unsigned(op.beat);
			_samplesAfterBeat=int((op.beat-_beat)*_samplesPerBeat);
			for(auto line: _activeLines){
				line->i=0;
				while(line->events[line->i].beat<op.beat) ++line->i;
			}
			processNexts();
			break;
		case Op::SILENCE:{
			std::vector<unsigned char> message;
			message.push_back(0x80);
			message.push_back(0);
			message.push_back(127);
			for(unsigned i=0; i<Sonic::MIDI_NOTES; ++i){
				message[1]=i;
				for(auto j: _channelToSonic){
					message[0]&=0xf0;
					message[0]|=j.first;
					j.second->processMidi(message);
				}
			}
			break;
		}
		case Op::REC_MAKE:{
			Rec& rec=_recPairs[_currentRecPair][(_currentRec+1)%2];
			for(unsigned i=0; i<rec.size; ++i)
				op.rec->push_back(rec.samples[i]);
			break;
		}
		case Op::REC:
			_activeRecs.push_back(op.rec);
			break;
		case Op::UNREC:
			_removeRecs.push_back(op.rec);
			break;
		case Op::REC_SWITCH:
			_switchRecPair=true;
			break;
		default: break;
	}
}

void Processor::processNexts(){
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
	//update active lines
	for(auto line: _nextLines) _activeLines.push_back(line);
	_nextLines.clear();
	for(auto i: _removeLines)
		for(auto j=_activeLines.begin(); j!=_activeLines.end(); ++j)
			if(i==*j){
				_activeLines.erase(j);
				break;
			}
	_removeLines.clear();
	//update active records
	for(auto rec: _nextRecs) _activeRecs.push_back(rec);
	_nextRecs.clear();
	for(auto i: _removeRecs)
		for(auto j=_activeRecs.begin(); j!=_activeRecs.end(); ++j)
			if(i==*j){
				_activeRecs.erase(j);
				break;
			}
	_removeRecs.clear();
	//records
	_currentRec=(_currentRec+1)%2;
	if(_switchRecPair){
		_currentRecPair=(_currentRecPair+1)%2;
		_switchRecPair=false;
	}
	Rec& rec=_recPairs[_currentRecPair][_currentRec];
	rec.clear();
	_recSample=0;
}

void Processor::allocateNextRecPair(unsigned size){
	if(size==0) return;
	const unsigned maxSize=_sampleRate*120;
	_recPairs[(_currentRecPair+1)%2][0].reserve(size);
	_recPairs[(_currentRecPair+1)%2][1].reserve(size);
	_queue.write(Op(Op::REC_SWITCH));
}

}//namespace dlal
