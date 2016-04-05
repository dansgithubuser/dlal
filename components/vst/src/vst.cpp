#include <vst.hpp>

#ifdef DLAL_WINDOWS
	#include <windows.h>
#endif

#include <SFML/Window.hpp>

#include <cassert>
#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <thread>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Vst; }

namespace dlal{

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
		#ifdef DLAL_WINDOWS
			HMODULE library=LoadLibraryExA((LPCSTR)s.c_str(), NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
			if(!library) return "error: couldn't load library, error code "+std::to_string(GetLastError());
			typedef Plugin* (*Vst2xPluginMain)(Vst2xHostCallback);
			Vst2xPluginMain pluginMain;
			for(auto i: {"VSTPluginMain", "VstPluginMain()", "main"}){
				pluginMain=(Vst2xPluginMain)GetProcAddress(library, i);
				if(pluginMain) break;
			}
			if(!pluginMain) return "error: couldn't get plugin's main";
			operateOnPlugin([this, &pluginMain]()->std::string{ _plugin=pluginMain(vst2xHostCallback); return ""; });
		#else
				return "error: unsupported platform";
		#endif
		if(_plugin->magic!=('V'<<24|'s'<<16|'t'<<8|'P')) return "error: wrong magic number";
		return operateOnPlugin([this]()->std::string{
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
			std::string result;
			_plugin->dispatcher(_plugin, 42, 0, (int*)&arrangement, &arrangement, 0.0f);
			_plugin->dispatcher(_plugin, 12, 0, (int*)1, NULL, 0.0f);//audio processing on
			_plugin->dispatcher(_plugin, 71, 0, (int*)0, NULL, 0.0f);//audio processing start
			return result;
		});
	});
	registerCommand("show", "", [this](std::stringstream& ss){
		sf::Window window(sf::VideoMode(800, 600), "dlal vst");
		operateOnPlugin([this, &window](){
			_plugin->dispatcher(_plugin, 14, 0, (int*)0, window.getSystemHandle(), 0.0f);
			while(window.isOpen()){
				sf::Event event;
				while(window.pollEvent(event)) if(event.type==sf::Event::Closed) window.close();
				std::this_thread::sleep_for(std::chrono::milliseconds(1));
			}
			return "";
		});
		return "";
	});
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return _hostCallbackExpected.is_lock_free()?"lockless":"lockfull";
	});
}

void Vst::evaluate(){
	for(auto output: _outputs){
		memcpy(_i.data()[0], output->audio(), _samplesPerEvaluation*sizeof(float));
		memcpy(_i.data()[1], output->audio(), _samplesPerEvaluation*sizeof(float));
		operateOnPlugin([this]()->std::string{
			_plugin->processReplacing(_plugin, _i.data(), _o.data(), _samplesPerEvaluation);
			return "";
		});
		for(unsigned i=0; i<_samplesPerEvaluation; ++i) output->audio()[i]=_o.data()[0][i]+_o.data()[1][i];
	}
	_samples+=_samplesPerEvaluation;
	double quarters=_samplesPerEvaluation/_samplesPerBeat/_beatsPerQuarter;
	_startToNowInQuarters+=quarters;
	_lastBarToNowInQuarters+=quarters;
	double quartersPerBar=1.0*_beatsPerBar/_beatsPerQuarter;
	if(_lastBarToNowInQuarters>quartersPerBar) _lastBarToNowInQuarters-=quartersPerBar;
}

void Vst::midi(const uint8_t* bytes, unsigned size){
	if(size>=4) return;
	MidiEvent midiEvent(1/*realtime*/, bytes, size);
	Events events;
	events.size=1;
	events.reserved=0;
	events.events[0]=(Event*)&midiEvent;
	operateOnPlugin([this, &events](){
		if(!_plugin->dispatcher(_plugin, 25, 0, (int*)0, &events, 0.0f))
			std::cerr<<"midi failed"<<std::endl;
		return "";
	});
}

int* Vst::vst2xHostCallback(
	Plugin* effect, int32_t opcode, int32_t index, int* value, void* data, float opt
){
	if(!_hostCallbackExpected){
		const char* message="host callback called unexpectedly";
		std::cerr<<message<<std::endl;
		throw std::runtime_error(message);
	}
	#ifdef DLAL_VST_TEST
		std::cout<<"callback - opcode "<<opcode<<" index "<<index<<" value "<<value<<" data "<<data<<" opt "<<opt<<std::flush;
	#endif
	void* result=(void*)0;
	switch(opcode){
		case 0: break;//parameter updated
		case 1: result=(void*)2400; break;//version 2.4
		case 3: break;//idle
		case 6: break;//want midi
		case 7:{//get time
			static Vst2xTimeInfo timeInfo;
			timeInfo.startToNowInSamples=(double)_self->_samples;
			timeInfo.sampleRate=_self->_sampleRate;
			timeInfo.systemTimeInNanoseconds=double(std::chrono::system_clock::now().time_since_epoch()/std::chrono::nanoseconds(1));
			timeInfo.startToNowInQuarters=_self->_startToNowInQuarters;
			timeInfo.tempo=60*_self->_sampleRate/_self->_samplesPerBeat;
			timeInfo.startToLastBarInQuarters=_self->_startToNowInQuarters-_self->_lastBarToNowInQuarters;
			timeInfo.timeSigTop=_self->_beatsPerBar;
			timeInfo.timeSigBottom=_self->_beatsPerQuarter*4;
			double samplesPer24=_self->_samplesPerBeat*_self->_beatsPerQuarter/24;
			double q24=_self->_startToNowInQuarters*24;
			timeInfo.nowToQuarter24thInSamples=int32_t(-samplesPer24*(q24-std::floor(q24)));
			timeInfo.flags=(unsigned(value)&0xaf00)|0x02;
			result=&timeInfo;
			break;
		}
		case 16: result=(void*)_self->_sampleRate; break;
		case 17: result=(void*)_self->_samplesPerEvaluation; break;
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

Vst* Vst::_self;
std::atomic<unsigned> Vst::_hostCallbackExpected=0;

std::string Vst::operateOnPlugin(std::function<std::string()> f){
	_self=this;
	++_hostCallbackExpected;
	#ifdef DLAL_VST_TEST
		std::cout<<"plugin operation starting"<<std::endl;
	#endif
	auto r=f();
	#ifdef DLAL_VST_TEST
		std::cout<<"plugin operation finished"<<std::endl;
	#endif
	--_hostCallbackExpected;
	return r;
}

}//namespace dlal
