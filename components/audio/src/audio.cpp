#include "audio.hpp"

#include <algorithm>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Audio; }

static int paStreamCallback(
	const void* input,
	void* output,
	unsigned long samples,
	const PaStreamCallbackTimeInfo* timeInfo,
	PaStreamCallbackFlags status,
	void* userData
){
	dlal::Audio* audio=(dlal::Audio*)userData;
	audio->_input=(float*)input;
	audio->_output=(float*)output;
	std::fill_n(audio->_output, samples, 0.0f);
	audio->_system->evaluate();
	return paContinue;
}

static std::string paError(const PaError& err){
	Pa_Terminate();
	std::stringstream ss;
	ss<<"PortAudio error number: "<<err<<"\n";
	ss<<"PortAudio error message: "<<Pa_GetErrorText(err);
	return ss.str();
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
	addJoinAction([this](System& system){
		return system.set(_sampleRate, _log2SamplesPerCallback);
	});
	registerCommand("set", "sampleRate <log2(samples per callback)>",
		[this](std::stringstream& ss){
			ss>>_sampleRate;
			ss>>_log2SamplesPerCallback;
			return "";
		}
	);
	registerCommand("start", "", [this](std::stringstream& ss)->std::string{
		if(!_system) return "error: must add before starting";
		if(_started) return "already started";
		return start();
	});
	registerCommand("finish", "", [this](std::stringstream& ss)->std::string{
		if(!_started) return "not started";
		return finish();
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
	unsigned samples=1<<_log2SamplesPerCallback;
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
	PaError err;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError) return "error: Pa_Initialize failed: "+paError(err);
	//get wasapi if it exists
	PaHostApiIndex apiIndex=Pa_GetDefaultHostApi();
	if(apiIndex<0) return "error: no default host API: "+paError(apiIndex);
	for(PaHostApiIndex i=0; i<Pa_GetHostApiCount(); ++i)
		if(Pa_GetHostApiInfo(i)->type==paWASAPI){ apiIndex=i; break; }
	//input
	PaStreamParameters inputParameters;
	inputParameters.device=Pa_GetHostApiInfo(apiIndex)->defaultInputDevice;
	if(inputParameters.device==paNoDevice)
		return "error: no default input device: "+paError(err);
	inputParameters.channelCount=1;
	inputParameters.sampleFormat=PA_SAMPLE_FORMAT;
	inputParameters.suggestedLatency=
		Pa_GetDeviceInfo(inputParameters.device)->defaultLowInputLatency;
	inputParameters.hostApiSpecificStreamInfo=NULL;
	//output
	PaStreamParameters outputParameters;
	outputParameters.device=Pa_GetHostApiInfo(apiIndex)->defaultOutputDevice;
	if(outputParameters.device==paNoDevice)
		return "error: no default output device: "+paError(err);
	outputParameters.channelCount=1;
	outputParameters.sampleFormat=PA_SAMPLE_FORMAT;
	outputParameters.suggestedLatency=
		Pa_GetDeviceInfo(outputParameters.device)->defaultLowOutputLatency;
	outputParameters.hostApiSpecificStreamInfo=NULL;
	//open stream
	err=Pa_OpenStream(
		&_paStream,
		&inputParameters,
		&outputParameters,
		_sampleRate,
		1<<_log2SamplesPerCallback,
		paNoFlag,
		paStreamCallback,
		this
	);
	if(err!=paNoError) return "error: Pa_OpenStream failed: "+paError(err);
	//start stream
	err=Pa_StartStream(_paStream);
	if(err!=paNoError) return "error: Pa_StartStream failed: "+paError(err);
	_started=true;
	return "";
}

std::string Audio::finish(){
	PaError err;
	err=Pa_CloseStream(_paStream);
	if(err!=paNoError) return "error: "+paError(err);
	Pa_Terminate();
	_started=false;
	return "";
}

}//namespace dlal
