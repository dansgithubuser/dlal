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
	if(audio->_micReceiver){
		if(input){
			const float* inputF=(const float*)input;
			std::copy(inputF, inputF+samples, audio->_micReceiver->readAudio());
		}
		else{
			std::fill_n(audio->_micReceiver->readAudio(), samples, 0.0f);
			++audio->_underflows;
		}
	}
	audio->_output=(float*)output;
	audio->_system->evaluate(samples);
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
	_output((float*)1),//so readAudio isn't null when connecting
	_micReceiver(nullptr),
	_sampleRate(0),
	_underflows(0),
	_started(false)
	#ifdef TEST_AUDIO
		,_test(false)
	#endif
{
	registerCommand("set", "sampleRate log2SamplesPerCallback",
		[&](std::stringstream& ss){
			ss>>_sampleRate;
			ss>>_log2SamplesPerCallback;
			return "";
		}
	);
	registerCommand("start", "", [&](std::stringstream& ss)->std::string{
		if(!_system) return "error: must add before starting";
		if(_started) return "error: already started";
		return start();
	});
	registerCommand("finish", "", [&](std::stringstream& ss)->std::string{
		if(!_started) return "error: not started";
		return finish();
	});
	#ifdef TEST_AUDIO
		registerCommand("test", "", [&](std::stringstream& ss){
			_testPhase=0.0f;
			_test=true;
			return "";
		});
	#endif
}

Audio::~Audio(){ if(_started) finish(); }

std::string Audio::addInput(Component* component){
	if(std::count(_inputs.begin(), _inputs.end(), component))
		return "input already added";
	_inputs.push_back(component);
	return "";
}

std::string Audio::addOutput(Component* component){
	if(!component->readAudio()) return "error: output must receive audio";
	_micReceiver=component;
	return "";
}

std::string Audio::readyToEvaluate(){
	if(!_sampleRate)
		return "error: must set sample rate and log2 samples per callback";
	return "";
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
	std::fill_n(_output, samples, 0.0f);
	for(unsigned j=0; j<_inputs.size(); ++j){
		float* audio=_inputs[j]->readAudio();
		if(!audio) continue;
		for(unsigned i=0; i<samples; ++i) _output[i]+=audio[i];
	}
}

float* Audio::readAudio(){ return _output; }

std::string Audio::start(){
	PaError err;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError) return "error: Pa_Initialize failed: "+paError(err);
	//input
	PaStreamParameters inputParameters;
	inputParameters.device=Pa_GetDefaultInputDevice();
	if(inputParameters.device==paNoDevice)
		return "error: no default input device: "+paError(err);
	inputParameters.channelCount=1;
	inputParameters.sampleFormat=PA_SAMPLE_FORMAT;
	inputParameters.suggestedLatency=
		Pa_GetDeviceInfo(inputParameters.device)->defaultLowInputLatency;
	inputParameters.hostApiSpecificStreamInfo=NULL;
	//output
	PaStreamParameters outputParameters;
	outputParameters.device=Pa_GetDefaultOutputDevice();
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
