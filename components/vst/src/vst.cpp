#include <vst.hpp>

#ifdef DLAL_WINDOWS
	#include <windows.h>
#endif

#include <chrono>
#include <cmath>
#include <stdexcept>

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
		_i.resize(_samplesPerEvaluation, 0.0f);
		return "";
	});
	registerCommand("load", "<vst>", [this](std::stringstream& ss)->std::string{
		std::string s;
		ss>>s;
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
			if(!_plugin->dispatcher(_plugin, 42, 0, (int*)&arrangement, &arrangement, 0.0f))
				return "error: couldn't set speaker arrangement";
			_plugin->dispatcher(_plugin, 12, 0, (int*)1, NULL, 0.0f);//audio processing on
			_plugin->dispatcher(_plugin, 71, 0, (int*)0, NULL, 0.0f);//audio processing start
			return "";
		});
	});
	registerCommand("lockless", "", [this](std::stringstream& ss){
		return _hostCallbackExpected.is_lock_free()?"lockless":"lockfull";
	});
}

Vst::~Vst(){}

void Vst::evaluate(){
	for(auto output: _outputs){
		memcpy(_i.data(), output->audio(), _samplesPerEvaluation*sizeof(float));
		float* i=_i.data();
		float* o=output->audio();
		operateOnPlugin([this, &i, &o]()->std::string{ _plugin->processReplacing(_plugin, &i, &o, _samplesPerEvaluation); return ""; });
	}
	_samples+=_samplesPerEvaluation;
	double quarters=_samplesPerEvaluation/_samplesPerBeat/_beatsPerQuarter;
	_startToNowInQuarters+=quarters;
	_lastBarToNowInQuarters+=quarters;
	double quartersPerBar=1.0*_beatsPerBar/_beatsPerQuarter;
	if(_lastBarToNowInQuarters>quartersPerBar) _lastBarToNowInQuarters-=quartersPerBar;
}

void Vst::midi(const uint8_t* bytes, unsigned size){
}

int* Vst::vst2xHostCallback(
	Plugin* effect, int32_t opcode, int32_t index, int* value, void* data, float opt
){
	if(!_hostCallbackExpected) throw std::runtime_error("host callback called unexpectedly");
	switch(opcode){
		case 1: return (int*)2400;//version 2.4
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
			return (int*)&timeInfo;
		}
		case 16: return (int*)_self->_sampleRate;
		case 17: return (int*)_self->_samplesPerEvaluation;
		case 23: break;//get current process level - unknown
		case 24: break;//get automation state - unsupported
		case 32: strcpy((char*)data, "dan"); break;//get vendor string
		case 33: strcpy((char*)data, "dlal"); break;//get product string
		case 38: return (int*)1;//get language - english
		default:
			_self->_system->report(dlal::System::RC_IN_EVALUATION, "unhandled opcode "+std::to_string(opcode));
			break;
	}
	return (int*)0;
}

Vst* Vst::_self;
std::atomic<bool> Vst::_hostCallbackExpected;

std::string Vst::operateOnPlugin(std::function<std::string()> f){
	_self=this;
	_hostCallbackExpected=true;
	auto r=f();
	_hostCallbackExpected=false;
	return r;
}

}//namespace dlal
