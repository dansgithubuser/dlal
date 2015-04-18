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
	if(input){
	}
	else ++audio->_underflows;
	audio->_output=(float*)output;
	std::fill_n(audio->_output, samples, 0.0f);
	audio->_system->evaluate(samples);
	return paContinue;
}

static std::string paError(const PaError& err){
	Pa_Terminate();
	std::stringstream ss;
	ss<<"PortAudio error number: "<<err;
	ss<<"PortAudio error message: "<<Pa_GetErrorText(err);
	return ss.str();
}

namespace dlal{

Audio::Audio():
	_output((float*)1),
	_sampleRate(0),
	_underflows(0),
	_started(false)
	#ifdef TEST_AUDIO
		,_test(false)
	#endif
{}

bool Audio::ready(){
	if(_sampleRate) return true;
	_text="must set sample rate and log2 samples per callback";
	return false;
}

void Audio::addInput(Component* component){
	std::stringstream ss;
	ss<<"sampleRate "<<_sampleRate;
	component->sendText(ss.str());
	_inputs.push_back(component);
}

void Audio::evaluate(unsigned samples){
	#ifdef TEST_AUDIO
		if(_test){
			for(unsigned i=0; i<samples; ++i){
				_output[i]=_testPhase;
				_testPhase+=2*440.0f/_sampleRate;
				if(_testPhase>=1.0f) _testPhase-=2.0f;
			}
			return;
		}
	#endif
	for(unsigned i=0; i<samples; ++i) _output[i]=0.0f;
	for(unsigned j=0; j<_inputs.size(); ++j){
		const float* audio=_inputs[j]->readAudio();
		if(audio) for(unsigned i=0; i<samples; ++i) _output[i]+=audio[i];
		const std::string* text=_inputs[j]->readText();
		if(text) process(*text);
	}
}

float* Audio::readAudio(){ return _output; }

std::string* Audio::readText(){ return &_text; }

void Audio::clearText(){ _text.clear(); }

void Audio::sendText(const std::string& text){ process(text); }

void Audio::start(){
	PaError err;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError){
		_text="Pa_Initialize failed: "+paError(err);
		return;
	}
	//input
	PaStreamParameters inputParameters;
	inputParameters.device=Pa_GetDefaultInputDevice();
	if(inputParameters.device==paNoDevice){
		_text="no default input device: "+paError(err);
		return;
	}
	inputParameters.channelCount=1;
	inputParameters.sampleFormat=PA_SAMPLE_FORMAT;
	inputParameters.suggestedLatency=
		Pa_GetDeviceInfo(inputParameters.device)->defaultLowInputLatency;
	inputParameters.hostApiSpecificStreamInfo=NULL;
	//output
	PaStreamParameters outputParameters;
	outputParameters.device=Pa_GetDefaultOutputDevice();
	if(outputParameters.device==paNoDevice){
		_text="no default output device: "+paError(err);
		return;
	}
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
	if(err!=paNoError){
		_text="Pa_OpenStream failed: "+paError(err);
		return;
	}
	//start stream
	err=Pa_StartStream(_paStream);
	if(err!=paNoError){
		_text="Pa_StartStream failed: "+paError(err);
		return;
	}
	_started=true;
}

void Audio::finish(){
	PaError err;
	err=Pa_CloseStream(_paStream);
	if(err!=paNoError){
		_text=paError(err);
		return;
	}
	Pa_Terminate();
	_started=false;
}

void Audio::process(const std::string& text){
	std::stringstream ss(text);
	std::string s;
	ss>>s;
	if(s=="set"){
		ss>>_sampleRate;
		ss>>_log2SamplesPerCallback;
	}
	else if(s=="start"){
		if(!_system){
			_text="must add before starting";
			return;
		}
		if(_started){
			_text="already started";
			return;
		}
		start();
	}
	else if(s=="finish"){
		if(!_started){
			_text="not started";
			return;
		}
		finish();
	}
	#ifdef TEST_AUDIO
		else if(s=="test"){
			_testPhase=0.0f;
			_test=true;
		}
	#endif
	else _text="unrecognized command";
}

std::string Audio::commands(){
	return
		"set start finish"
		#ifdef TEST_AUDIO
			" test"
		#endif
	;
}

}//namespace dlal
