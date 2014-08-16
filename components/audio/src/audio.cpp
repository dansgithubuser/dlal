#include "audio.hpp"

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
	audio->_system->evaluate(samples);
	return paContinue;
}

static std::string paError(const PaError& err){
	Pa_Terminate();
	std::stringstream ss;
	ss<<"PortAudio error number: "<<err<<"\n";
	ss<<"PortAudio error message: "<<Pa_GetErrorText(err)<<"\n";
	return ss.str();
}

namespace dlal{

Audio::Audio(): _underflows(0), _test(false) {}

void Audio::addInput(Component* component){
	std::stringstream ss;
	ss<<"sampleRate "<<_sampleRate;
	component->sendText(ss.str());
	_inputs.push_back(component);
}

void Audio::evaluate(unsigned samples){
	if(_test){
		for(unsigned i=0; i<samples; ++i){
			_output[i]=_testPhase;
			_testPhase+=2*440.0f/_sampleRate;
			if(_testPhase>=1.0f) _testPhase-=2.0f;
		}
		return;
	}
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

void Audio::sendText(const std::string& text){ process(text); }

void Audio::start(std::stringstream& ss){
	//parameters
	ss>>_sampleRate;
	unsigned log2SamplesPerCallback;
	ss>>log2SamplesPerCallback;
	//
	PaError err;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError){
		_text="Pa_Initialize failed\n"+paError(err);
		return;
	}
	//input
	PaStreamParameters inputParameters;
	inputParameters.device=Pa_GetDefaultInputDevice();
	if(inputParameters.device==paNoDevice){
		_text="no default input device\n"+paError(err);
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
		_text="no default output device\n"+paError(err);
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
		1<<log2SamplesPerCallback,
		paNoFlag,
		paStreamCallback,
		this
	);
	if(err!=paNoError){
		_text="Pa_OpenStream failed\n"+paError(err);
		return;
	}
	//start stream
	err=Pa_StartStream(_paStream);
	if(err!=paNoError){
		_text="Pa_StartStream failed\n"+paError(err);
		return;
	}
}

void Audio::finish(){
	PaError err;
	err=Pa_CloseStream(_paStream);
	if(err!=paNoError){
		_text=paError(err);
		return;
	}
	Pa_Terminate();
}

void Audio::process(const std::string& text){
	std::stringstream ss(text);
	std::string s;
	ss>>s;
	if(s=="start") start(ss);
	else if(s=="finish") finish();
	else if(s=="test"){
		_testPhase=0.0f;
		_test=true;
	}
	else _text="unrecognized command\n";
}

}//namespace dlal
