#include "audio.hpp"

#include <portaudio.h>

#include <iostream>
#include <cstring>

typedef float Sample;

static const PaSampleFormat PA_SAMPLE_FORMAT=paFloat32;

static PaStream* fPaStream;
static std::function<void(const float* input, float* output)> fCallback;

#ifdef DEBUG_UNDERFLOWS
	static unsigned underflows=0;
#endif

static int paStreamCallback(
	const void* input,
	void* output,
	unsigned long samples,
	const PaStreamCallbackTimeInfo* timeInfo,
	PaStreamCallbackFlags status,
	void* userData
){
	//underflow
	if(!input){
		for(unsigned long i=0; i<samples; ++i) ((Sample*)output)[i]=0;
		#ifdef DEBUG_UNDERFLOWS
			++underflows;
		#endif
		return paContinue;
	}
	//normal processing
	fCallback((const Sample*)input, (Sample*)output);
	//
	return paContinue;
}

static void paError(const PaError& err){
	Pa_Terminate();
	std::cerr<<"PortAudio error number: "<<err<<"\n";
	std::cerr<<"PortAudio error message: "<<Pa_GetErrorText(err)<<"\n";
}

namespace dlal{

void audioInit(
	std::function<void(const float* input, float* output)> callback,
	unsigned sampleRate,
	unsigned log2SamplesPerCallback
){
	PaStreamParameters inputParameters, outputParameters;
	PaError err;
	fCallback=callback;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError){
		std::cerr<<"audio error: Pa_Initialize failed\n";
		paError(err);
		return;
	}
	//input
	inputParameters.device=Pa_GetDefaultInputDevice();
	if(inputParameters.device==paNoDevice){
		std::cerr<<"audio error: no default input device\n";
		paError(err);
		return;
	}
	inputParameters.channelCount=1;
	inputParameters.sampleFormat=PA_SAMPLE_FORMAT;
	inputParameters.suggestedLatency=Pa_GetDeviceInfo(inputParameters.device)->defaultLowInputLatency;
	inputParameters.hostApiSpecificStreamInfo=NULL;
	//output
	outputParameters.device=Pa_GetDefaultOutputDevice();
	if(outputParameters.device==paNoDevice){
		std::cerr<<"audio error: no default output device\n";
		paError(err);
		return;
	}
	outputParameters.channelCount=1;
	outputParameters.sampleFormat=PA_SAMPLE_FORMAT;
	outputParameters.suggestedLatency=Pa_GetDeviceInfo(outputParameters.device)->defaultLowOutputLatency;
	outputParameters.hostApiSpecificStreamInfo=NULL;
	//open stream
	err=Pa_OpenStream(
		&fPaStream,
		&inputParameters,
		&outputParameters,
		sampleRate,
		1<<log2SamplesPerCallback,
		paNoFlag,
		paStreamCallback,
		NULL
	);
	if(err!=paNoError){
		std::cerr<<"audio error: Pa_OpenStream failed\n";
		paError(err);
		return;
	}
	//start stream
	err=Pa_StartStream(fPaStream);
	if(err!=paNoError){
		std::cerr<<"audio error: Pa_StartStream failed\n";
		paError(err);
		return;
	}
}

void audioFinish(){
	PaError err;
	err=Pa_CloseStream(fPaStream);
	if(err!=paNoError){
		paError(err);
		return;
	}
	#ifdef DEBUG_UNDERFLOWS
		std::cout<<"underflows: "<<underflows<<"\n";
	#endif
	Pa_Terminate();
}

}//namespace dlal
