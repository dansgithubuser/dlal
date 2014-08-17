#include "audio.hpp"

#include "portaudio.h"
#include "RtMidi.h"

#include <iostream>
#include <cstring>

typedef float Sample;

static const PaSampleFormat PA_SAMPLE_FORMAT=paFloat32;

static const unsigned LOG2_SAMPLES_PER_CALLBACK=6;
static const unsigned SAMPLE_RATE=44100;

static PaStream* paStream;
static RtMidiIn* rtMidiIn = nullptr;

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
	for(unsigned long i=0; i<samples; ++i){
		((Sample*)output)[i]=((Sample*)input)[i];
	}
	//
	return paContinue;
}

static void rtMidiCallback (double deltatime, std::vector<unsigned char>* message, void* userData)
{
	unsigned int nBytes = message->size();
	for (unsigned int i = 0; i<nBytes; i++)
		std::cout << "Byte " << i << " = " << (int)message->at(i) << ", ";
	if (nBytes > 0)
		std::cout << "stamp = " << deltatime << std::endl;
}

static void paError(const PaError& err){
	Pa_Terminate();
	std::cerr<<"PortAudio error number: "<<err<<"\n";
	std::cerr<<"PortAudio error message: "<<Pa_GetErrorText(err)<<"\n";
}

namespace dlal{

void init(){
	PaStreamParameters inputParameters, outputParameters;
	PaError err;
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
		&paStream,
		&inputParameters,
		&outputParameters,
		SAMPLE_RATE,
		1<<LOG2_SAMPLES_PER_CALLBACK,
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
	err=Pa_StartStream(paStream);
	if(err!=paNoError){
		std::cerr<<"audio error: Pa_StartStream failed\n";
		paError(err);
		return;
	}

	try
	{
		rtMidiIn = new RtMidiIn();
	} 
	catch (RtMidiError& error) 
	{
		error.printMessage();
		return;
	}

	unsigned int nPorts = rtMidiIn->getPortCount();
	std::cout << "Midi in port count: " << nPorts << std::endl;
	for (unsigned int i = 0; i < nPorts; i++)
	{
		std::string portname = rtMidiIn->getPortName(i);
		std::cout << "Port " << i << ": " << portname << std::endl;	
	}
	
	if (nPorts < 1)
	{
		return;
	}
	
	rtMidiIn->openPort(0);
	rtMidiIn->setCallback(rtMidiCallback);
}

void finish(){
	PaError err;
	err=Pa_CloseStream(paStream);
	if(err!=paNoError){
		paError(err);
		return;
	}
	#ifdef DEBUG_UNDERFLOWS
		std::cout<<"underflows: "<<underflows<<"\n";
	#endif
	Pa_Terminate();

	delete rtMidiIn;
}

}//namespace dlal
