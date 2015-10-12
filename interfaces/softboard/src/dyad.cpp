#include <dyad.h>

#include <thread>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <algorithm>
#include <vector>
#include <cstdlib>

bool fReady, fGood, fQuit;
dyad_Stream* fStream;
std::thread fThread;
std::mutex fMutex;

static void onReady(dyad_Event* e){
	fGood=true;
}

static void onDestroyed(dyad_Event* e){
	fGood=false;
}

static void onError(dyad_Event* e){
	std::cerr<<"dyad error: "<<e->msg<<"\n";
	fGood=false;
}

static void onPanic(const char* message){
	std::cerr<<"dyad panic: "<<message<<"\n";
	fGood=false;
}

bool dyadInit(std::string ip, int port){
	fReady=false;
	fGood=true;
	fQuit=false;
	dyad_atPanic(onPanic);
	dyad_init();
	if(!fGood) return false;
	fStream=dyad_newStream();
	dyad_addListener(fStream, DYAD_EVENT_READY  , onReady    , NULL);
	dyad_addListener(fStream, DYAD_EVENT_DESTROY, onDestroyed, NULL);
	dyad_addListener(fStream, DYAD_EVENT_ERROR  , onError    , NULL);
	dyad_connect(fStream, ip.c_str(), port);
	dyad_setUpdateTimeout(0.001);
	fThread=std::thread([](){
		while(!fQuit&&fGood){
			fMutex.lock();
			dyad_update();
			fMutex.unlock();
		}
	});
	return true;
}

bool dyadFinish(){
	fQuit=true;
	fThread.join();
	dyad_shutdown();
	return fGood;
}

bool dyadCheck(){ return fGood; }

bool dyadWrite(std::string s){
	if(!s.size()) return fGood;
	static std::vector<uint8_t> bytes;
	bytes.resize(4+s.size());
	bytes[0]=(s.size()>>0x00)&0xff;
	bytes[1]=(s.size()>>0x08)&0xff;
	bytes[2]=(s.size()>>0x10)&0xff;
	bytes[3]=(s.size()>>0x18)&0xff;
	std::copy(s.begin(), s.end(), bytes.begin()+4);
	fMutex.lock();
	dyad_write(fStream, bytes.data(), bytes.size());
	fMutex.unlock();
	return fGood;
}
