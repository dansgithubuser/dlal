#include "audio.hpp"

#include <algorithm>
#include <stdexcept>

DLAL_BUILD_COMPONENT_DEFINITION(Audio)

static int rtAudioCallback(
	void* output,
	void* input,
	unsigned samples,
	double time,
	RtAudioStreamStatus status,
	void* userData
){
	if(status) input=NULL;
	dlal::Audio* audio=(dlal::Audio*)userData;
	audio->_input=(float*)input;
	audio->_output=(float*)output;
	std::fill_n(audio->_output, samples, 0.0f);
	audio->_system->evaluate();
	for(int i=samples-1; i>=0; --i){
		float f=audio->_output[i];
		if(f<-1.0f) f=-1.0f;
		else if(f>1.0f) f=1.0f;
		audio->_output[2*i+0]=f;
		audio->_output[2*i+1]=f;
	}
	return 0;
}

static uint8_t ilog2(int x){
	int result=-1;
	while(x){
		x>>=1;
		++result;
	}
	if(result==-1) throw std::logic_error("input outside domain");
	return result;
}

namespace dlal{

Audio::Audio():
	_sampleRate(0),
	_started(false),
	_underflows(0)
	#ifdef DLAL_AUDIO_TEST
		,_test(false)
	#endif
{
	_checkAudio=true;
	addJoinAction([this](System& system)->std::string{
		if(
			!_sampleRate
			&&
			system._variables.count("sampleRate")
			&&
			system._variables.count("samplesPerEvaluation")
		){
			_sampleRate=std::stoi(system._variables.at("sampleRate"));
			_log2SamplesPerEvaluation=ilog2(std::stoi(system._variables.at("samplesPerEvaluation")));
			return "";
		}
		return system.set(_sampleRate, _log2SamplesPerEvaluation);
	});
	registerCommand("set", "sampleRate <log2(samples per evaluation)>",
		[this](std::stringstream& ss){
			ss>>_sampleRate;
			ss>>_log2SamplesPerEvaluation;
			return "";
		}
	);
	registerCommand("start", "", [this](std::stringstream& ss)->std::string{
		if(!_system) return "error: must add before starting";
		if(_started) return "already started";
		auto s=_system->prep();
		if(isError(s)) return s;
		return start();
	});
	registerCommand("finish", "", [this](std::stringstream& ss)->std::string{
		if(!_started) return "not started";
		return finish();
	});
	registerCommand("underflows", "", [this](std::stringstream&){
		std::stringstream ss;
		ss<<_underflows;
		return ss.str();
	});
	#ifdef DLAL_AUDIO_TEST
		registerCommand("test", "", [this](std::stringstream& ss){
			_testPhase=0.0f;
			_test=true;
			return "";
		});
	#endif
}

void Audio::evaluate(){
	unsigned samples=1<<_log2SamplesPerEvaluation;
	if(_input) add(_input, samples, _outputs);
	else{
		for(auto i: _outputs)
			if(i->audio()) std::fill_n(i->audio(), samples, 0.0f);
		++_underflows;
	}
	#ifdef DLAL_AUDIO_TEST
		if(_test){
			for(unsigned i=0; i<samples; ++i){
				_output[i]=_testPhase;
				_testPhase+=2*440.0f/_sampleRate;
				if(_testPhase>=1.0f) _testPhase-=2.0f;
			}
			return;
		}
	#endif
}

std::string Audio::start(){
	if(_rtAudio.getDeviceCount()<1) return "error: no audio devices found";
	RtAudio::StreamParameters iParams, oParams;
	iParams.deviceId=_rtAudio.getDefaultInputDevice (); iParams.nChannels=1;
	oParams.deviceId=_rtAudio.getDefaultOutputDevice(); oParams.nChannels=2;
	unsigned samples=1<<_log2SamplesPerEvaluation;
	try{ _rtAudio.openStream(
		&oParams,
		&iParams,
		RTAUDIO_FLOAT32,
		_sampleRate,
		&samples,
		rtAudioCallback,
		this
	); }
	catch(RtAudioError& e){ return std::string("error: ")+e.getMessage(); }
	if(samples!=1<<_log2SamplesPerEvaluation)
		return "error: couldn't get desired samples per evaluation";
	try{ _rtAudio.startStream(); }
	catch(RtAudioError& e){ return std::string("error: ")+e.getMessage(); }
	_started=true;
	return "";
}

std::string Audio::finish(){
	_rtAudio.closeStream();
	_started=false;
	return "";
}

}//namespace dlal
