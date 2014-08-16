#include <cmath>
#include <cstdio>

#include "portaudio.h"

using namespace std;

#define DEBUG 0
#define PA_SAMPLE_TYPE paFloat32

const int FRAME_SIZE=64;
const int SAMPLE_RATE=44100;

const int OVERLAP=64;

const float MIN_BSN_FREQ=55.0f;
const float MAX_BSN_FREQ=440.0f;
const float MAX_BSN_PERIOD=SAMPLE_RATE/MIN_BSN_FREQ;
const float MIN_BSN_PERIOD=SAMPLE_RATE/MAX_BSN_FREQ;

typedef float SAMPLE;

#if DEBUG
	static int underflows=0;
#endif

class Window{
	public:
		~Window(){ delete[] buffer; }
		void init(int _maxSize){
			maxSize=_maxSize;
			buffer=new SAMPLE[maxSize];
			currentSize=0;
			currentSample=0;
		}
		SAMPLE take(float increment){
			float result=buffer[int(currentSample)];
			currentSample+=increment;
			return result;
		}
		void put(SAMPLE s){ buffer[currentSize++]=s; }
		void clear(){
			currentSize=0;
			currentSample=0;
		}
		int size(){ return currentSize; }
		bool full(){ return currentSize==maxSize; }
		bool done(){ return int(currentSample)>=maxSize; }
		float readCurrentSample(){ return currentSample; }
	private:
		SAMPLE* buffer;
		int currentSize, maxSize;
		float currentSample;
};

class SignalProcessor{
	public:
		SignalProcessor(int frameSize);
		~SignalProcessor();
		void process(const SAMPLE* input, SAMPLE* output);
	private:
		int otherWindow(int i){ return 1-i; }
		int frameSize;
		Window windows[2];
		int playWindow;
		int recordWindow;
};

SignalProcessor::SignalProcessor(int frameSize):
	frameSize(frameSize),
	playWindow(0),
	recordWindow(0)
{
	windows[0].init(int(MAX_BSN_PERIOD)+OVERLAP);
	windows[1].init(int(MAX_BSN_PERIOD)+OVERLAP);
}

SignalProcessor::~SignalProcessor(){}

void SignalProcessor::process(const SAMPLE* input, SAMPLE* output){
	for(int i=0; i<frameSize; ++i){
		//record
		if(windows[recordWindow].done()) windows[recordWindow].clear();
		if(!windows[recordWindow].full()){
			windows[recordWindow].put(input[i]);
			if(windows[recordWindow].full())
				recordWindow=otherWindow(recordWindow);
		}
		//output
		output[i]=windows[playWindow].take(0.5f);
		//window switching
		if(windows[playWindow].readCurrentSample()>MAX_BSN_PERIOD/2){
			
		}
		//switch play windows
		if(windows[playWindow].done())
			playWindow=otherWindow(playWindow);
	}
}

static int callback(
	const void* inputBuffer,
	void* outputBuffer,
	unsigned long framesPerBuffer,
	const PaStreamCallbackTimeInfo* timeInfo,
	PaStreamCallbackFlags statusFlags,
	void* userData
){
	if(!inputBuffer){
		//silence
		SAMPLE* out=(SAMPLE*)outputBuffer;
		for(unsigned i=0; i<framesPerBuffer; ++i){
			*out=0;
			++out;
		}
		#if DEBUG
			++underflows;
		#endif
	}
	else{
		((SignalProcessor*) userData)->process((SAMPLE*) inputBuffer, (SAMPLE*) outputBuffer);
	}
	return paContinue;
}

void error(const PaError& err){
	Pa_Terminate();
	fprintf(stderr, "An error occured while using the portaudio stream\n");
	fprintf(stderr, "Error number: %d\n", err);
	fprintf(stderr, "Error message: %s\n", Pa_GetErrorText(err));
}

int main(){
	PaStreamParameters inputParameters, outputParameters;
	PaStream* stream;
	PaError err;
	//initialize
	err=Pa_Initialize();
	if(err!=paNoError){
		error(err);
		return -1;
	}
	//input
	inputParameters.device=Pa_GetDefaultInputDevice();
	if(inputParameters.device==paNoDevice){
		fprintf(stderr, "Error: No default input device.\n");
		error(err);
		return -1;
	}
	inputParameters.channelCount=1;
	inputParameters.sampleFormat=PA_SAMPLE_TYPE;
	inputParameters.suggestedLatency=Pa_GetDeviceInfo(inputParameters.device)->defaultLowInputLatency;
	inputParameters.hostApiSpecificStreamInfo=NULL;
	//output
	outputParameters.device=Pa_GetDefaultOutputDevice();
	if(outputParameters.device==paNoDevice){
		fprintf(stderr, "Error: No default output device.\n");
		error(err);
		return -1;
	}
	outputParameters.channelCount=1;
	outputParameters.sampleFormat=PA_SAMPLE_TYPE;
	outputParameters.suggestedLatency=Pa_GetDeviceInfo(outputParameters.device)->defaultLowOutputLatency;
	outputParameters.hostApiSpecificStreamInfo=NULL;
	//signal processor
	SignalProcessor signalProcessor(FRAME_SIZE);
	//open stream
	err=Pa_OpenStream(
		&stream,
		&inputParameters,
		&outputParameters,
		SAMPLE_RATE,
		FRAME_SIZE,
		paNoFlag,
		callback,
		&signalProcessor
	);
	if(err!=paNoError){
		error(err);
		return -1;
	}
	//start stream
	err=Pa_StartStream(stream);
	if(err!=paNoError){
		error(err);
		return -1;
	}
	//wait for character
	printf("Hit ENTER to stop program.\n");
	getchar();
	//stop
	err=Pa_CloseStream(stream);
	if(err!=paNoError){
		error(err);
		return -1;
	}
	printf("Finished.\n");
	#if DEBUG
		printf("underflows: %d\n", underflows);
	#endif
	Pa_Terminate();
	//let user read results
	printf("Hit ENTER to quit.\n");
	getchar();
	return 0;
}
