#include "network.hpp"

#include <vector>
#include <sstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Network; }

static void onData(dyad_Event* e){
	int i=0;
	while(i<e->size){
		uint32_t size=
			(e->data[0]<<0x00)|
			(e->data[1]<<0x08)|
			(e->data[2]<<0x10)|
			(e->data[3]<<0x18);
		i+=4;
		std::stringstream ss;
		for(unsigned j=0; j<size; ++j) ss<<(char)e->data[i++];
		((dlal::Network*)e->udata)->queue(dlal::Page(ss));
	}
}

static void onDestroyed(dyad_Event* e){
	using namespace dlal;
	Network* network=(Network*)e->udata;
	network->_system->report(System::RC_IN_DYAD, "error: server destroyed", network);
}

static void onError(dyad_Event* e){
	using namespace dlal;
	Network* network=(Network*)e->udata;
	network->_system->report(System::RC_IN_DYAD, "error: "+std::string(e->msg), network);
}

static void onAccept(dyad_Event* e){
	((dlal::Network*)e->udata)->_system->dyadAddListener(
		e->remote, DYAD_EVENT_DATA, onData, e->udata
	);
}

namespace dlal{

Network::Network(): _port(9089), _queue(8) {
	addJoinAction([this](System&)->std::string{
		return dyadPauseAnd([this]()->std::string{
			dyad_Stream* server=_system->dyadNewStream();
			_system->dyadAddListener(server, DYAD_EVENT_ACCEPT , onAccept   , this);
			_system->dyadAddListener(server, DYAD_EVENT_ERROR  , onError    , this);
			_system->dyadAddListener(server, DYAD_EVENT_DESTROY, onDestroyed, this);
			if(_system->dyadListenEx(server, "0.0.0.0", _port, 511)<0)
				return "error: couldn't listen";
			return "";
		});
	});
	registerCommand("port", "", [this](std::stringstream& ss)->std::string{
		ss>>_port;
		return "";
	});
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return _queue.lockless()?"lockless":"lockfull";
	});
	registerCommand("map_midi", "<key> <midi bytes>", [this](std::stringstream& ss){
		std::string key;
		ss>>key;
		std::vector<uint8_t> midi;
		unsigned byte;
		while(ss>>byte) midi.push_back(byte);
		_map[key]=dlal::Page(midi.data(), midi.size(), 0);
		return "";
	});
	registerCommand("map_command", "<key> <command>", [this](std::stringstream& ss){
		std::string key;
		ss>>key;
		std::string command;
		ss.ignore(1);
		std::getline(ss, command);
		_map[key]=dlal::Page(command, 0);
		return "";
	});
}

void Network::evaluate(){
	Page page;
	if(_queue.read(page, true)){
		if(page._type==dlal::Page::TEXT&&_map.count(page._text))
			page=_map[page._text];
		page.dispatch(*this, _outputs, _samplesPerEvaluation);
	}
}

void Network::queue(const Page& page){ _queue.write(page); }

}//namespace dlal
