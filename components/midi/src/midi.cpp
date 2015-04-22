#include "midi.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Midi; }

static void rtMidiCallback(double delta, std::vector<unsigned char>* message, void* userData){
	dlal::Midi* midi=(dlal::Midi*)userData;
	midi->queue(dlal::MidiMessage(*message));
}

namespace dlal{

Midi::Midi(): _rtMidiIn(nullptr), _queue(7) {
	registerCommand("midi", "byte[1]..byte[n]", [&](std::stringstream& ss){
		MidiMessage message;
		unsigned byte, i=0;
		while(ss>>std::hex>>byte&&i<MidiMessage::SIZE){
			message._bytes[i]=byte;
			++i;
		}
		queue(message);
		return "";
	});
	registerCommand("ports", "", [&](std::stringstream& ss){
		std::string s;
		s=allocate();
		if(s.size()) return s;
		s="";
		for(unsigned i=0; i<_rtMidiIn->getPortCount(); ++i)
			s+=_rtMidiIn->getPortName(i)+"\n";
		return s;
	});
	registerCommand("open", "port", [&](std::stringstream& ss)->std::string{
		std::string s;
		s=allocate();
		if(s.size()) return s;
		_rtMidiIn->setCallback(rtMidiCallback, this);
		s="";
		ss>>s;
		for(unsigned i=0; i<_rtMidiIn->getPortCount(); ++i)
			if(_rtMidiIn->getPortName(i).find(s)!=std::string::npos){
				_rtMidiIn->openPort(i);
				return "";
			}
		return "error: couldn't find requested port";
	});
}

Midi::~Midi(){ if(_rtMidiIn) delete _rtMidiIn; }

void Midi::evaluate(unsigned samples){
	_messages.clear();
	MidiMessage message;
	while(_queue.read(message, true)) _messages.push_back(message);
}

MidiMessages* Midi::readMidi(){ return &_messages; }

void Midi::queue(const MidiMessage& message){
	_queue.write(message);
}

std::string Midi::allocate(){
	if(_rtMidiIn) return "";
	try{ _rtMidiIn=new RtMidiIn(); }
	catch(RtMidiError& error){
		_rtMidiIn=nullptr;
		return "error: "+error.getMessage();
	}
	return "";
}

}//namespace dlal
