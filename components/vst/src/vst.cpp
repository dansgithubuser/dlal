#include <vst.hpp>

#ifdef DLAL_WINDOWS
	#include <windows.h>
#elif defined(DLAL_OSX)
	#include <Foundation/Foundation.h>
	#include <AppKit/AppKit.h>
#elif defined(DLAL_LINUX)
	#include <dlfcn.h>
#endif

#include <SFML/Window.hpp>

#include <cassert>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <thread>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Vst; }

namespace dlal{

#ifdef DLAL_OSX
	template<typename T> class Releaser{
		public:
			Releaser(T t): _(t) {}
			~Releaser(){ if(_) CFRelease(_); }
			operator T(){ return _; }
		protected:
			T _;
	};
#endif

struct Vst2xSpeakerProperties{
	float azimuth, elevation, radius, reserved;
	char name[64];
	int32_t type;
	char future[28];
};

struct Vst2xSpeakerArrangement{
	int32_t type, channels;
	Vst2xSpeakerProperties properties[8];
};

struct Vst2xTimeInfo{
	double
		startToNowInSamples, sampleRate,
		systemTimeInNanoseconds,
		startToNowInQuarters,
		tempo,
		startToLastBarInQuarters,
		startToCycleStartInQuarters, startToCycleEndInQuarters
	;
	int32_t
		timeSigTop, timeSigBottom,
		smpteStartToNow, smpteFrameRate,
		nowToQuarter24thInSamples,
		flags
	;
};

#define EVENT_HEADER int32_t type, size, delta, flags;

struct Event{
	EVENT_HEADER
	char data[16];
};

struct MidiEvent{
	MidiEvent(uint32_t flags, const uint8_t* bytes, unsigned size):
		type(1), size(sizeof(MidiEvent)), delta(0), flags(flags),
		noteDuration(0), offset(0), detune(0), noteOffVelocity(0), reserved1(0), reserved2(0)
	{
		memset(midi, 0, sizeof(midi));
		assert(size<4);
		memcpy(midi, bytes, size);
	}
	EVENT_HEADER
	int32_t noteDuration, offset;
	char midi[4], detune, noteOffVelocity, reserved1, reserved2;
};

struct Events{
	int32_t size;
	int* reserved;
	Event* events[2];
};

struct Rect{ int16_t top, left, bottom, right; };

Vst::Vst():
	_samples(0),
	_samplesPerBeat(22050),
	_beatsPerBar(4),
	_beatsPerQuarter(1),
	_startToNowInQuarters(0),
	_lastBarToNowInQuarters(0)
{
	_checkAudio=true;
	addJoinAction([this](System&){
		const int defaultChannels=2;
		_i.resize(defaultChannels, _samplesPerEvaluation);
		_o.resize(defaultChannels, _samplesPerEvaluation);
		return "";
	});
	registerCommand("load", "<vst>", [this](std::stringstream& ss)->std::string{
		std::string s;
		ss>>std::ws;
		std::getline(ss, s);
		setSelf(nullptr);
		typedef Plugin* (*Vst2xPluginMain)(Vst2xHostCallback);
		Vst2xPluginMain pluginMain;
		#ifdef DLAL_WINDOWS
		{
			HMODULE library=LoadLibraryExA((LPCSTR)s.c_str(), NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
			if(!library) return "error: couldn't load library, error code "+std::to_string(GetLastError());
			for(auto i: {"VSTPluginMain", "VstPluginMain()", "main"}){
				pluginMain=(Vst2xPluginMain)GetProcAddress(library, i);
				if(pluginMain) break;
			}
		}
		#elif defined(DLAL_OSX)
		{
			Releaser<CFStringRef> path=CFStringCreateWithCString(NULL, s.c_str(), kCFStringEncodingASCII);
			if(!path) return "error: couldn't create string";
			Releaser<CFURLRef> url=CFURLCreateWithFileSystemPath(kCFAllocatorDefault, path, kCFURLPOSIXPathStyle, true);
			if(!url) return "error: couldn't create URL";
			CFBundleRef bundle=CFBundleCreate(kCFAllocatorDefault, url);
			if(!bundle) return "error: couldn't create bundle";
			pluginMain=(Vst2xPluginMain)CFBundleGetFunctionPointerForName(bundle, CFSTR("VSTPluginMain"));
			if(!pluginMain) pluginMain=(Vst2xPluginMain)CFBundleGetFunctionPointerForName(bundle, CFSTR("main_macho"));
		}
		#elif defined(DLAL_LINUX)
			auto handle=dlopen(s.c_str(), RTLD_LOCAL|RTLD_NOW);
			if(!handle) return "error: couldn't load library";
			for(auto i: {"VSTPluginMain", "main"}){
				pluginMain=(Vst2xPluginMain)dlsym(handle, i);
				if(pluginMain) break;
			}
		#else
			return "error: unsupported platform";
		#endif
		if(!pluginMain) return "error: couldn't get plugin's main";
		_plugin=pluginMain(vst2xHostCallback);
		if(_plugin->magic!=('V'<<24|'s'<<16|'t'<<8|'P')) return "error: wrong magic number";
		setSelf(_plugin);
		Vst2xSpeakerProperties properties;
		properties.azimuth=0;
		properties.elevation=0;
		strcpy(properties.name, "speaker");
		properties.radius=1.0f;
		properties.type=0;//mono
		Vst2xSpeakerArrangement arrangement;
		arrangement.type=0;//mono
		arrangement.channels=1;
		arrangement.properties[0]=properties;
		_plugin->dispatcher(_plugin, 42, 0, (int*)&arrangement, &arrangement, 0.0f);
		_plugin->dispatcher(_plugin, 12, 0, (int*)1, nullptr, 0.0f);//audio processing on
		_plugin->dispatcher(_plugin, 71, 0, (int*)0, nullptr, 0.0f);//audio processing start
		return "";
	});
	registerCommand("show", "", [this](std::stringstream& ss){
		Rect* rect=nullptr;
		_plugin->dispatcher(_plugin, 13, 0, (int*)0, &rect, 0.0f);
		unsigned width=800, height=600;
		if(rect){
			width=rect->right-rect->left;
			height=rect->bottom-rect->top;
		}
		#ifdef DLAL_OSX
			static NSWindow* window;
			window=[
				[NSWindow alloc]
				initWithContentRect: NSMakeRect(0, 0, width, height)
				styleMask: NSTitledWindowMask|NSClosableWindowMask
				backing: NSBackingStoreBuffered
				defer: NO
			];
			[window makeKeyAndOrderFront: NSApp];
			auto windowHandle=(__bridge void*)[window contentView];
		#else
			sf::Window window(sf::VideoMode(width, height), "dlal vst");
			auto windowHandle=window.getSystemHandle();
		#endif
		_plugin->dispatcher(_plugin, 14, 0, (int*)0, (void*)windowHandle, 0.0f);
		#ifndef DLAL_OSX
			while(window.isOpen()){
				sf::Event event;
				while(window.pollEvent(event)) if(event.type==sf::Event::Closed) window.close();
				std::this_thread::sleep_for(std::chrono::milliseconds(1));
			}
		#endif
		return "";
	});
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return (
			_samples.is_lock_free()
			&&
			_samplesPerBeat.is_lock_free()
			&&
			_beatsPerBar.is_lock_free()
		)?"lockless":"lockfull";
	});
	registerCommand("list", "", [this](std::stringstream& ss){
		std::vector<std::string> names, displays, labels;
		std::vector<float> values;
		std::vector<uint8_t> automatables;
		unsigned maxNameSize=0;
		for(int32_t i=0; i<_plugin->params; ++i){
			auto s=getString(8, i);
			if(s.size()>maxNameSize) maxNameSize=s.size();
			names.push_back(s);
			displays.push_back(getString(7, i));
			labels.push_back(getString(6, i));
			values.push_back(_plugin->getParameter(_plugin, i));
			automatables.push_back((uint8_t)(ptrdiff_t)_plugin->dispatcher(_plugin, 26, i, nullptr, nullptr, 0.0f));
		}
		std::stringstream result;
		for(unsigned i=0; i<names.size(); ++i){
			result<<std::setw(unsigned(std::log10(_plugin->params))+2)<<i<<" ";
			result<<std::setw(maxNameSize)<<names[i]<<": ";
			result<<displays[i]<<" ("<<labels[i]<<") ["<<values[i]<<"] ";
			if(!automatables[i]) result<<"UNAUTOMATABLE";
			result<<"\n";
		}
		return result.str();
	});
	registerCommand("get", "<parameter index>", [this](std::stringstream& ss){
		int32_t i;
		ss>>i;
		std::stringstream tt;
		tt<<_plugin->getParameter(_plugin, i);
		return tt.str();
	});
	registerCommand("set", "<parameter index> <value>", [this](std::stringstream& ss){
		int32_t i;
		float value;
		ss>>i>>value;
		_plugin->setParameter(_plugin, i, value);
		return "";
	});
	registerCommand("set_program", "<program number>", [this](std::stringstream& ss){
		int i;
		ss>>i;
		if(_plugin->dispatcher(_plugin, 67, 0, nullptr, nullptr, 0.0f)){
			_plugin->dispatcher(_plugin, 2, 0, nullptr, nullptr, 0.0f);
			_plugin->dispatcher(_plugin, 68, 0, nullptr, nullptr, 0.0f);
			return "";
		}
		return "couldn't set program";
	});
	registerCommand("get_programs", "", [this](std::stringstream& ss){
		std::stringstream tt;
		const int32_t programs=_plugin->programs;
		for(int32_t i=0; i<programs; ++i){
			tt<<std::setw(unsigned(std::log10(programs))+2)<<i<<": ";
			tt<<getString(29, i)<<"\n";
		}
		return tt.str();
	});
}

void Vst::evaluate(){
	for(auto output: _outputs){
		memcpy(_i.data()[0], output->audio(), _samplesPerEvaluation*sizeof(float));
		memcpy(_i.data()[1], output->audio(), _samplesPerEvaluation*sizeof(float));
		_plugin->processReplacing(_plugin, _i.data(), _o.data(), _samplesPerEvaluation);
		for(unsigned i=0; i<_samplesPerEvaluation; ++i) output->audio()[i]=_o.data()[0][i]+_o.data()[1][i];
	}
	_samples+=_samplesPerEvaluation;
	double quarters=_samplesPerEvaluation/_samplesPerBeat/_beatsPerQuarter;
	_startToNowInQuarters=_startToNowInQuarters+quarters;
	_lastBarToNowInQuarters=_lastBarToNowInQuarters+quarters;
	double quartersPerBar=1.0*_beatsPerBar/_beatsPerQuarter;
	if(_lastBarToNowInQuarters>quartersPerBar) _lastBarToNowInQuarters=_lastBarToNowInQuarters-quartersPerBar;
}

void Vst::midi(const uint8_t* bytes, unsigned size){
	if(size>=4) return;
	MidiEvent midiEvent(1/*realtime*/, bytes, size);
	Events events;
	events.size=1;
	events.reserved=0;
	events.events[0]=(Event*)&midiEvent;
	if(!_plugin->dispatcher(_plugin, 25, 0, (int*)0, &events, 0.0f)) std::cerr<<"midi failed"<<std::endl;
}

int* Vst::vst2xHostCallback(
	Plugin* plugin, int32_t opcode, int32_t index, int* value, void* data, float opt
){
	Vst* self;
	_mutex.lock();
	if(!_self.count(plugin)) self=_self[nullptr];
	else self=_self[plugin];
	_mutex.unlock();
	#ifdef DLAL_VST_TEST
		std::cout<<"callback - opcode "<<opcode<<" index "<<index<<" value "<<value<<" data "<<data<<" opt "<<opt<<std::flush;
	#endif
	void* result=(void*)0;
	switch(opcode){
		case 0: break;//parameter updated
		case 1: result=(void*)2400; break;//version 2.4
		case 3: break;//idle
		case 6: result=(void*)1; break;//want midi
		case 7:{//get time
			static Vst2xTimeInfo timeInfo;
			timeInfo.startToNowInSamples=(double)self->_samples;
			timeInfo.sampleRate=self->_sampleRate;
			timeInfo.systemTimeInNanoseconds=double(std::chrono::system_clock::now().time_since_epoch()/std::chrono::nanoseconds(1));
			timeInfo.startToNowInQuarters=self->_startToNowInQuarters;
			timeInfo.tempo=60*self->_sampleRate/self->_samplesPerBeat;
			timeInfo.startToLastBarInQuarters=self->_startToNowInQuarters-self->_lastBarToNowInQuarters;
			timeInfo.timeSigTop=self->_beatsPerBar;
			timeInfo.timeSigBottom=self->_beatsPerQuarter*4;
			double samplesPer24=self->_samplesPerBeat*self->_beatsPerQuarter/24;
			double q24=self->_startToNowInQuarters*24;
			timeInfo.nowToQuarter24thInSamples=int32_t(-samplesPer24*(q24-std::floor(q24)));
			timeInfo.flags=(ptrdiff_t(value)&0xaf00)|0x02;
			result=&timeInfo;
			break;
		}
		case 13: break;//plugin notifies inputs/outputs has changed - we assume all plugins have 2 or fewer outputs
		case 16: result=(void*)(ptrdiff_t)self->_sampleRate; break;
		case 17: result=(void*)(ptrdiff_t)self->_samplesPerEvaluation; break;
		case 23: break;//get current process level - unknown
		case 24: break;//get automation state - unsupported
		case 32: strcpy((char*)data, "dan"); break;//get vendor string
		case 33: strcpy((char*)data, "dlal"); break;//get product string
		case 37: if(!strcmp((char*)data, "receiveVstMidiEvent")) result=(void*)1; break;
		case 38: break;//get language - 0 means english
		case 42: break;//update display
		default:
			std::cerr<<"unhandled opcode "+std::to_string(opcode)<<std::endl;
			break;
	}
	#ifdef DLAL_VST_TEST
		std::cout<<" - returning "<<result<<std::endl;
	#endif
	return (int*)result;
}

std::map<Vst::Plugin*, Vst*> Vst::_self;
std::mutex Vst::_mutex;

void Vst::setSelf(Plugin* plugin){
	_mutex.lock();
	_self[plugin]=this;
	_mutex.unlock();
}

std::string Vst::getString(int32_t opcode, int32_t index){
	char s[32];
	_plugin->dispatcher(_plugin, opcode, index, nullptr, s, 0.0f);
	std::string result(s);
	result.erase(0, result.find_first_not_of(" \n\r\t"));
	result.erase(result.find_last_not_of(" \n\r\t")+1);
	return result;
}

}//namespace dlal
