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
	dlal::Page page;
	page.fromFile(ss);
	fStreamToNetwork[e->stream]->queue(page);
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

Network::Network(): _queue(8), _audio(1, 0.0f), _inited(false) {
	registerCommand("open", "port", [&](std::stringstream& ss)->std::string{
		if(!_inited){
			dyad_atPanic(onPanic);
			dyad_init();
			if(fMessage.size()) return fMessage;
			dyad_setUpdateTimeout(0.001);
			_quit=false;
			_thread=std::thread([&](){
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
	registerCommand("set", "<sample rate>", [&](std::stringstream& ss)->std::string{
		unsigned sampleRate;
		ss>>sampleRate;
		_audio.resize(sampleRate);
		return "";
	});
	registerCommand("check", "", [&](std::stringstream& ss)->std::string{
		return fMessage;
	});
}

Network::~Network(){
	if(_inited){
		_quit=true;
		_thread.join();
		dyad_shutdown();
	}
}

void Network::evaluate(unsigned samples){
	std::fill(_audio.begin(), _audio.end(), 0.0f);
	_midi.clear();
	_text.clear();
	Page page;
	if(_queue.read(page, true)){
		switch(page._type){
			case dlal::Page::AUDIO: _audio=page._audio; break;
			case dlal::Page::MIDI : _midi =page._midi ; break;
			case dlal::Page::TEXT : _text =page._text ; break;
			default: break;
		}
	}
}

float* Network::readAudio(){ return _audio.data(); }
MidiMessages* Network::readMidi(){ return &_midi; }
std::string* Network::readText(){ return &_text; }

void Network::queue(const Page& page){ _queue.write(page); }

}//namespace dlal
