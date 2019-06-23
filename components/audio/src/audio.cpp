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
	for(int i=0; i<samples; ++i){
		float& f=audio->_output[i];
		if(f<-1.0f) f=-1.0f;
		else if(f>1.0f) f=1.0f;
	}
	audio->_queue.write(audio->_output, samples);
	for(int i=samples-1; i>=0; --i){
		float f=audio->_output[i];
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
	_queue(0),
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
	registerCommand("buffer_resize", "log2Size", [this](std::stringstream& ss){
		unsigned log2Size;
		ss>>log2Size;
		_queue.resize(log2Size);
		return "";
	});
	registerCommand("buffer_get", "size", [this](std::stringstream& ss)->std::string{
		size_t size;
		ss>>size;
		//read from queue
		static std::vector<float> v;
		if(v.size()<size) v.resize(size);
		if(!_queue.read(v.data(), size, true)) return "error: underflow";
		//serialize
		std::stringstream result;
		const std::string digits="./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
		for(auto i: v){
			unsigned u=(i+1)*((1<<11)-1);
			result<<digits[u&0x3f]<<digits[u>>6];
		}
		return result.str();
	});
	registerCommand("probe", "", [this](std::stringstream&){
		std::stringstream ss;
		const auto devices=_rtAudio.getDeviceCount();
		ss<<"[\n";
		for(unsigned i=0; i<devices; ++i){
			RtAudio::DeviceInfo info=_rtAudio.getDeviceInfo(i);
			ss<<"\t{\n";
			ss<<"\t\t\""<<"probed"<<"\" : "<<info.probed<<" ,\n";
			ss<<"\t\t\""<<"name"<<"\" : \""<<info.name<<"\" ,\n";
			ss<<"\t\t\""<<"outputChannels"<<"\" : "<<info.outputChannels<<" ,\n";
			ss<<"\t\t\""<<"inputChannels"<<"\" : "<<info.inputChannels<<" ,\n";
			ss<<"\t\t\""<<"duplexChannels"<<"\" : "<<info.duplexChannels<<" ,\n";
			ss<<"\t\t\""<<"isDefaultOutput"<<"\" : "<<info.isDefaultOutput<<" ,\n";
			ss<<"\t\t\""<<"isDefaultInput"<<"\" : "<<info.isDefaultInput<<" ,\n";
			ss<<"\t\t\""<<"preferredSampleRate"<<"\" : "<<info.preferredSampleRate<<"\n";
			ss<<"\t}";
			if(i<devices-1) ss<<",";
			ss<<"\n";
		}
		ss<<"]";
		return ss.str();
	});
	registerCommand("start", "[input] [output]", [this](std::stringstream& ss)->std::string{
		if(!_system) return "error: must add before starting";
		if(_started) return "already started";
		auto s=_system->prep();
		if(isError(s)) return s;
		int input=-1, output=-1;
		ss>>input>>output;
		return start(input, output);
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

std::string Audio::start(int input, int output){
	if(input <0) input =_rtAudio.getDefaultInputDevice ();
	if(output<0) output=_rtAudio.getDefaultOutputDevice();
	if(_rtAudio.getDeviceCount()<1) return "error: no audio devices found";
	RtAudio::StreamParameters iParams, oParams;
	iParams.deviceId=input ; iParams.nChannels=1;
	oParams.deviceId=output; oParams.nChannels=2;
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
