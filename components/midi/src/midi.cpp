#include "midi.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Midi)

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
		for(unsigned i=0; i<_rtMidiIn->getPortCount(); ++i){
			std::string portName=_rtMidiIn->getPortName(i);
			if(portName.find(s)!=std::string::npos){
				_rtMidiIn->openPort(i);
				_portName=portName;
				return "";
			}
		}
		return "error: couldn't find requested port";
	});
	registerCommand("port", "", [this](std::stringstream& ss){
		return _portName;
	});
	registerCommand("blacklist", "output <nibbles; [=<>]x for some comparison with x, x for any>", [this](std::stringstream& ss)->std::string{
		return _blacklist.append(ss);
	});
	registerCommand("whitelist", "output <nibbles; [=<>]x for some comparison with x, x for any>", [this](std::stringstream& ss)->std::string{
		return _whitelist.append(ss);
	});
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return _queue.lockless()?"lockless":"lockfull";
	});
}

Midi::~Midi(){ if(_rtMidiIn) delete _rtMidiIn; }

static unsigned getNibble(const std::vector<uint8_t>& bytes, unsigned i){
	return (bytes.at(i/2)>>(i%2?4:0))&0xf;
}

void Midi::evaluate(){
	std::vector<uint8_t> midi;
	while(_queue.read(midi, true))
		for(unsigned i=0; i<_outputs.size(); ++i){
			if(_blacklist.match(i, midi)&&!_whitelist.match(i, midi)) continue;
			midiSend(_outputs.at(i), midi.data(), midi.size());
			_system->_reportQueue.write((std::string)"midi "+componentToStr(this)+" "+componentToStr(_outputs.at(i)));
		}
}

void Midi::midi(const uint8_t* bytes, unsigned size){
	_queue.write(std::vector<uint8_t>(bytes, bytes+size));
}


std::string Midi::List::append(std::stringstream& ss){
	unsigned output;
	ss>>output;
	if(_.size()<=output) _.resize(output+1);
	MidiPattern m;
	auto s=m.populate(ss);
	if(isError(s)) return s;
	_.at(output).push_back(m);
	return "";
}

bool Midi::List::match(unsigned output, const std::vector<uint8_t>& midi) const{
	if(output>=_.size()) return false;
	for(const auto& i: _.at(output)) if(i.match(midi)) return true;
	return false;
}

std::string Midi::List::MidiPattern::populate(std::stringstream& ss){
	std::string s;
	while(ss>>s){
		if(std::string("=<>").find(s)!=std::string::npos){
			unsigned n;
			ss>>std::hex>>n;
			_.push_back(std::pair<char, unsigned>(s.at(0), n));
		}
		else if(s=="x"){
			_.push_back(std::pair<char, unsigned>('x', 0));
		}
		else return "unknown nibble specification";
	}
	return "";
}

bool Midi::List::MidiPattern::match(const std::vector<uint8_t>& midi) const{
	for(unsigned i=0; i<_.size(); ++i)
		switch(_.at(i).first){
			case 'x': break;
			case '=': if(getNibble(midi, i)!=_.at(i).second) return false;
			case '<': if(getNibble(midi, i)>=_.at(i).second) return false;
			case '>': if(getNibble(midi, i)<=_.at(i).second) return false;
			default: break;
		}
	return true;
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
