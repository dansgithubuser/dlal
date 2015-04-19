#include "midi.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Midi; }

static void rtMidiCallback(double delta, std::vector<unsigned char>* message, void* userData){
	dlal::Midi* midi=(dlal::Midi*)userData;
	midi->queue(dlal::MidiMessage(*message));
}

namespace dlal{

Midi::Midi(): _queue(7) {
	registerCommand("midi", "byte[1]..byte[n]", [&](std::stringstream& ss){
		MidiMessage message;
		unsigned byte, i=0;
		while(ss>>std::hex>>byte&&i<MidiMessage::SIZE){
			message._bytes[i]=byte;
			++i;
		}
		queue(message);
	});
	registerCommand("ports", "", [&](std::stringstream& ss){
		_text="";
		for(unsigned i=0; i<_rtMidiIn->getPortCount(); ++i)
			_text+=_rtMidiIn->getPortName(i)+"\n";
	});
	registerCommand("open", "port", [&](std::stringstream& ss){
		std::string s;
		ss>>s;
		for(unsigned i=0; i<_rtMidiIn->getPortCount(); ++i)
			if(_rtMidiIn->getPortName(i).find(s)!=std::string::npos){
				_rtMidiIn->openPort(i);
				_text="";
				return;
			}
		_text="error: couldn't find requested port";
	});
	try{ _rtMidiIn=new RtMidiIn(); }
	catch(RtMidiError& error){ _text="error: "+error.getMessage(); return; }
	_rtMidiIn->setCallback(rtMidiCallback, this);
	_text="";
}

Midi::~Midi(){ delete _rtMidiIn; }

void Midi::evaluate(unsigned samples){
	_messages.clear();
	MidiMessage message;
	while(_queue.read(message, true)) _messages.push_back(message);
}

MidiMessages* Midi::readMidi(){ return &_messages; }

std::string* Midi::readText(){ return &_text; }

void Midi::queue(const MidiMessage& message){
	_queue.write(message);
}

}//namespace dlal
