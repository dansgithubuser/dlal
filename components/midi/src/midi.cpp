#include "midi.hpp"

#include <sstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Midi; }

static void rtMidiCallback(double delta, std::vector<unsigned char>* message, void* userData){
	dlal::Midi* midi=(dlal::Midi*)userData;
	midi->queue(dlal::MidiMessage(*message));
}

namespace dlal{

Midi::Midi(): _queue(7) {
	try{
		_rtMidiIn=new RtMidiIn();
	}
	catch(RtMidiError& error){
		_text="error: "+error.getMessage();
		return;
	}
	if(_rtMidiIn->getPortCount()<1){
		_text="error: no midi input ports";
		return;
	}
	_rtMidiIn->openPort(0);
	_rtMidiIn->setCallback(rtMidiCallback);
}

Midi::~Midi(){ delete _rtMidiIn; }

void Midi::evaluate(unsigned samples){
	_messages.clear();
	MidiMessage message;
	while(_queue.read(message, true)) _messages.push_back(message);
}

MidiMessages* Midi::readMidi(){ return &_messages; }

std::string* Midi::readText(){ return &_text; }

void Midi::clearText(){ _text.clear(); }

bool Midi::sendText(const std::string& text){
	std::stringstream ss(text);
	std::string s;
	ss>>s;
	if(s=="midi"){
		MidiMessage message;
		unsigned byte, i=0;
		while(ss>>std::hex>>byte&&i<MidiMessage::SIZE){
			message._bytes[i]=byte;
			++i;
		}
		queue(message);
	}
	else return false;
	return true;
}

std::string Midi::commands(){ return "midi"; }

void Midi::queue(const MidiMessage& message){
	_queue.write(message);
}

}//namespace dlal
