#include "network.hpp"

#include <dyad.h>

#include <algorithm>
#include <cstdint>
#include <sstream>
#include <map>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Network; }

static std::string fMessage;
static std::map<dyad_Stream*, dlal::Network*> fStreamToNetwork;

static void onData(dyad_Event* e){
	uint32_t size=
		(e->data[0]<<0x00)|
		(e->data[1]<<0x08)|
		(e->data[2]<<0x10)|
		(e->data[3]<<0x18);
	if(e->size!=4+size){
		fMessage="error: off kilter!";
		return;
	}
	std::stringstream ss;
	for(int i=4; i<e->size; ++i) ss<<(char)e->data[i];
	fStreamToNetwork[e->stream]->queue(dlal::Page(ss));
}

static void onDestroyed(dyad_Event* e){
	if(fStreamToNetwork.count(e->stream)) fMessage="error: server destroyed!";
}

static void onError(dyad_Event* e){
	fMessage="error: "+std::string(e->msg);
}

static void onAccept(dyad_Event* e){
	fStreamToNetwork[e->remote]=fStreamToNetwork[e->stream];
	dyad_addListener(e->remote, DYAD_EVENT_DATA, onData, NULL);
}

static void onPanic(const char* message){
	fMessage="error: (panic) "+std::string(message);
}

namespace dlal{

Network::Network(): _queue(8), _inited(false) {
	registerCommand("open", "port", [this](std::stringstream& ss)->std::string{
		if(!_inited){
			dyad_atPanic(onPanic);
			dyad_init();
			if(fMessage.size()) return fMessage;
			dyad_setUpdateTimeout(0.001);
			_quit=false;
			_thread=std::thread([this](){
				while(!_quit){
					_mutex.lock();
					dyad_update();
					_mutex.unlock();
				}
			});
			_inited=true;
		}
		_mutex.lock();
		dyad_Stream* serverStream=dyad_newStream();
		dyad_addListener(serverStream, DYAD_EVENT_ACCEPT , onAccept   , NULL);
		dyad_addListener(serverStream, DYAD_EVENT_ERROR  , onError    , NULL);
		dyad_addListener(serverStream, DYAD_EVENT_DESTROY, onDestroyed, NULL);
		int port;
		ss>>port;
		if(dyad_listenEx(serverStream, "127.0.0.1", port, 511)<0) return NULL;
		fStreamToNetwork[serverStream]=this;
		_mutex.unlock();
		return "";
	});
	registerCommand("check", "", [this](std::stringstream& ss)->std::string{
		return fMessage;
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

Network::~Network(){
	if(_inited){
		_quit=true;
		_thread.join();
		dyad_shutdown();
	}
}

void Network::evaluate(){
	Page page;
	if(_queue.read(page, true)){
		#ifdef TEST
			std::stringstream ss;
			page.toFile(ss);
			printf("%s\n", ss.str().c_str());
		#else
			if(page._type==dlal::Page::TEXT&&_map.count(page._text))
				page=_map[page._text];
			page.dispatch(_samplesPerEvaluation, _outputs);
		#endif
	}
}

void Network::queue(const Page& page){ _queue.write(page); }

}//namespace dlal
