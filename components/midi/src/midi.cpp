#include "midi.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Midi; }

static void rtMidiCallback(
	double delta, std::vector<unsigned char>* message, void* userData
){
	dlal::Midi* midi=(dlal::Midi*)userData;
	midi->midi(message->data(), message->size());
}

namespace dlal{

Midi::Midi(): _rtMidiIn(nullptr), _queue(7) {
	registerCommand("ports", "", [this](std::stringstream& ss){
		std::string s;
		s=allocate();
		if(s.size()) return s;
		s="";
		for(unsigned i=0; i<_rtMidiIn->getPortCount(); ++i)
			s+=_rtMidiIn->getPortName(i)+"\n";
		return s;
	});
	registerCommand("open", "port", [this](std::stringstream& ss)->std::string{
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
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return _queue.lockless()?"lockless":"lockfull";
	});
}

Midi::~Midi(){ if(_rtMidiIn) delete _rtMidiIn; }

void Midi::evaluate(){
	std::vector<uint8_t> midi;
	while(_queue.read(midi, true))
		for(auto output: _outputs){
			output->midi(midi.data(), midi.size());
			_system->_reportQueue.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(output));
		}
}

void Midi::midi(const uint8_t* bytes, unsigned size){
	_queue.write(std::vector<uint8_t>(bytes, bytes+size));
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
