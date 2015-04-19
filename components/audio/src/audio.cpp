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
		const float* inputF=(const float*)input;
		std::copy(inputF, inputF+samples, audio->_micReceiver->readAudio());
	}
	else{
		std::fill_n(audio->_micReceiver->readAudio(), samples, 0.0f);
		++audio->_underflows;
	}
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
	_output((float*)1),//so that readAudio doesn't return nullptr inappropriately
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
			_text="";
		}
	);
	registerCommand("start", "", [&](std::stringstream& ss){
		if(!_system){ _text="error: must add before starting"; return; }
		if(_started){ _text="error: already started"; return; }
		start();
	});
	registerCommand("finish", "", [&](std::stringstream& ss){
		if(!_started){ _text="error: not started"; return; }
		finish();
	});
	registerCommand("sampleRate", "", [&](std::stringstream& ss){
		if(!_sampleRate)
			{ _text="error: sample rate not set when requested"; return; }
		std::stringstream sampleRateSs;
		sampleRateSs<<_sampleRate;
		_text=sampleRateSs.str();
	});
	#ifdef TEST_AUDIO
		registerCommand("test", "", [&](std::stringstream& ss){
			_testPhase=0.0f;
			_test=true;
			_text="";
		});
	#endif
}

bool Audio::ready(){
	if(!_sampleRate){
		_text="error: must set sample rate and log2 samples per callback";
		return false;
	}
	_text="";
	return true;
}

void Audio::addInput(Component* component){
	_text="";
	if(std::count(_inputs.begin(), _inputs.end(), component)) return;
	_inputs.push_back(component);
}

void Audio::addOutput(Component* component){
	if(!component->readAudio())
		{ _text="error: output must receive audio"; return; }
	_text="";
	_micReceiver=component;
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
		float* audio=_inputs[j]->readAudio();
		if(!audio) continue;
		for(unsigned i=0; i<samples; ++i) _output[i]+=audio[i];
	}
}

float* Audio::readAudio(){ return _output; }

std::string* Audio::readText(){ return &_text; }

void Audio::start(){
	PaError err;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError){
		_text="error: Pa_Initialize failed: "+paError(err);
		return;
	}
	//input
	PaStreamParameters inputParameters;
	inputParameters.device=Pa_GetDefaultInputDevice();
	if(inputParameters.device==paNoDevice){
		_text="error: no default input device: "+paError(err);
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
		_text="error: no default output device: "+paError(err);
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
		_text="error: Pa_OpenStream failed: "+paError(err);
		return;
	}
	//start stream
	err=Pa_StartStream(_paStream);
	if(err!=paNoError){
		_text="error: Pa_StartStream failed: "+paError(err);
		return;
	}
	_started=true;
	_text="";
}

void Audio::finish(){
	PaError err;
	err=Pa_CloseStream(_paStream);
	if(err!=paNoError){
		_text="error: "+paError(err);
		return;
	}
	Pa_Terminate();
	_started=false;
	_text="";
}

}//namespace dlal
