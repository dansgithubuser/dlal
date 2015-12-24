#include <dyad.h>

#include <cassert>
#include <iostream>
#include <mutex>
#include <thread>

namespace dryad{

class Client;
static Client* fClient=NULL;

static void onPanic(const char* message);
static void onConnected(dyad_Event* e);
static void onDestroyed(dyad_Event* e);
static void onError(dyad_Event* e);
static void onData(dyad_Event* e);

class Client{
	friend void onConnected(dyad_Event*);
	friend void onClosed(dyad_Event*);
	friend void onDestroyed(dyad_Event*);
	friend void onData(dyad_Event*);
	public:
		Client(std::string ip, int port):
			_ip(ip), _port(port), _timesConnected(0), _timesDisconnected(0)
		{
			assert(!fClient);
			fClient=this;
			dyad_atPanic(onPanic);
			dyad_init();
			dyad_setUpdateTimeout(0.0);
			connect();
			_quit=false;
			_thread=std::thread([this](){
				while(!_quit){
					_mutex.lock();
					dyad_update();
					_mutex.unlock();
					std::this_thread::sleep_for(std::chrono::milliseconds(1));
				}
			});
		}
		~Client(){
			_quit=true;
			_thread.join();
			dyad_shutdown();
		}
		void write(const std::vector<uint8_t>& v){
			_mutex.lock();
			dyad_write(_stream, v.data(), v.size());
			_mutex.unlock();
		}
		void writeSizedString(const std::string& s){
			if(!s.size()) return;
			static std::vector<uint8_t> bytes;
			bytes.resize(4+s.size());
			bytes[0]=(s.size()>>0x00)&0xff;
			bytes[1]=(s.size()>>0x08)&0xff;
			bytes[2]=(s.size()>>0x10)&0xff;
			bytes[3]=(s.size()>>0x18)&0xff;
			std::copy(s.begin(), s.end(), bytes.begin()+4);
			write(bytes);
		}
		bool readSizedString(std::string& s){
			std::lock_guard<std::recursive_mutex> lock(_mutex);
			if(_queue.size()<4) return false;
			uint32_t size=
				(_queue[0]<<0x00)|
				(_queue[1]<<0x08)|
				(_queue[2]<<0x10)|
				(_queue[3]<<0x18)
			;
			if(_queue.size()<4+size) return false;
			s=std::string((char*)&_queue[4], size);
			_queue.erase(_queue.begin(), _queue.begin()+4+size);
			return true;
		}
		unsigned timesConnected(){ return _timesConnected; }
		unsigned timesDisconnected(){ return _timesDisconnected; }
	private:
		void connect(){
			_stream=dyad_newStream();
			dyad_addListener(_stream, DYAD_EVENT_CONNECT, onConnected, NULL);
			dyad_addListener(_stream, DYAD_EVENT_DESTROY, onDestroyed, NULL);
			dyad_addListener(_stream, DYAD_EVENT_ERROR, onError, NULL);
			dyad_addListener(_stream, DYAD_EVENT_DATA, onData, NULL);
			dyad_connect(_stream, _ip.c_str(), _port);
		}
		void queue(uint8_t* data, unsigned size){ _queue.insert(_queue.end(), data, data+size); }
		std::string _ip;
		int _port;
		dyad_Stream* _stream;
		std::thread _thread;
		bool _quit;
		std::recursive_mutex _mutex;
		std::vector<uint8_t> _queue;
		unsigned _timesConnected, _timesDisconnected;
};

static void onPanic(const char* message){
	std::cerr<<"dyad panic: "<<message<<"\n";
	assert(false);
}

static void onConnected(dyad_Event* e){
	++fClient->_timesConnected;
}

static void onDestroyed(dyad_Event* e){
	std::this_thread::sleep_for(std::chrono::milliseconds(500));
	if(fClient->_timesConnected>fClient->_timesDisconnected) ++fClient->_timesDisconnected;
	if(!fClient->_quit) fClient->connect();
}

static void onError(dyad_Event* e){
	std::cerr<<"dyad error: "<<e->msg<<"\n";
}

static void onData(dyad_Event* e){
	fClient->queue((uint8_t*)e->data, e->size);
}

}//namespace dryad
