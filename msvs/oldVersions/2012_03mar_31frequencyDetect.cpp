#include <cmath>
#include <cstdio>

#include "portaudio.h"

using namespace std;

#define DEBUG 0
#define SYNTHESIZE_SINEWAVE_INPUT 1
const float synthesizedSinewaveFrequency=220.0f;

const float PI=3.14159f;

#define PA_SAMPLE_TYPE paFloat32

const int FRAME_SIZE=64;
const int SAMPLE_RATE=44100;

const float MIN_BSN_FREQ=55.0f;
const float MAX_BSN_FREQ=440.0f;
const float MAX_BSN_PERIOD=SAMPLE_RATE/MIN_BSN_FREQ;
const float MIN_BSN_PERIOD=SAMPLE_RATE/MAX_BSN_FREQ;

const float REPETITION_TRIGGER_ERROR=0.01f;
const float MAX_REPETITION_SCORE=MAX_BSN_PERIOD*REPETITION_TRIGGER_ERROR;

const int CIRCLEBUFFER_SIZE=int(MAX_BSN_PERIOD*3+1);

typedef float SAMPLE;

#if DEBUG
	static int underflows=0;
#endif

class CircleBuffer{
	public:
		CircleBuffer(int size): size(size){
			buffer=new SAMPLE[size];
			for(int i=0; i<size; ++i) buffer[i]=0;
			current=0;
		}
		~CircleBuffer(){
			delete[] buffer;
		}
		SAMPLE at(int i){
			return buffer[(i+current+size)%size];
		}
		int put(SAMPLE s){
			--current;
			current=(current+size)%size;
			buffer[current]=s;
			return current;
		}
	private:
		SAMPLE* buffer;
		int current, size;
};

class Array{
	public:
		Array(int maxSize){
			buffer=new SAMPLE[maxSize];
			currentSize=0;
		}
		~Array(){ delete[] buffer; }
		SAMPLE at(int i){ return buffer[i]; }
		void put(SAMPLE s){ buffer[currentSize++]=s; }
		void clear(){ currentSize=0; }
		int size(){ return currentSize; }
	private:
		SAMPLE* buffer;
		int currentSize;
};

class SignalProcessor{
	public:
		SignalProcessor(int frameSize);
		~SignalProcessor();
		void process(const SAMPLE* input, SAMPLE* output);
	private:
		int frameSize;
		SAMPLE lowPassed;
		int repetitionPivot;
		int samplesSinceRepetitionPivot;
		CircleBuffer repetitionBuffer;
		float previousRepetitionScore;
		bool scoreGotBetter;
};

SignalProcessor::SignalProcessor(int frameSize):
	frameSize(frameSize),
	lowPassed(0),
	repetitionPivot(0),
	samplesSinceRepetitionPivot(0),
	repetitionBuffer(CIRCLEBUFFER_SIZE),
	previousRepetitionScore(0),
	scoreGotBetter(false)
{}

SignalProcessor::~SignalProcessor(){}

void SignalProcessor::process(const SAMPLE* input, SAMPLE* output){
	for(int i=0; i<frameSize; ++i){
		lowPassed=lowPassed+SAMPLE(0.001)*(input[i]-lowPassed);
		int current=repetitionBuffer.put(lowPassed);
		if(samplesSinceRepetitionPivot>MIN_BSN_PERIOD*2){
			if(abs(repetitionBuffer.at(repetitionPivot)-lowPassed)<REPETITION_TRIGGER_ERROR){
				float newScore=0;
				for(int i=0; i<samplesSinceRepetitionPivot; ++i){
					newScore+=abs(repetitionBuffer.at(repetitionPivot+i)-repetitionBuffer.at(current+i));
					if(newScore>=MAX_REPETITION_SCORE) break;
				}
				if(newScore<MAX_REPETITION_SCORE){
					if(newScore<previousRepetitionScore) scoreGotBetter=true;
					else if(scoreGotBetter){
						printf("frequency: %d\n", SAMPLE_RATE/(samplesSinceRepetitionPivot/2));
						repetitionPivot=(repetitionPivot+samplesSinceRepetitionPivot/2)%CIRCLEBUFFER_SIZE;
						samplesSinceRepetitionPivot-=samplesSinceRepetitionPivot/2;
						scoreGotBetter=false;
					}
					previousRepetitionScore=newScore;
				}
			}
			if(samplesSinceRepetitionPivot>MAX_BSN_PERIOD*2){
				samplesSinceRepetitionPivot-=int(MAX_BSN_PERIOD);
				repetitionPivot=(repetitionPivot+int(MAX_BSN_PERIOD))%CIRCLEBUFFER_SIZE;
			}
		}
		++samplesSinceRepetitionPivot;
		output[i]=input[i];
	}
}

#ifdef SYNTHESIZE_SINEWAVE_INPUT
	float phase=0.0f;
#endif

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
		#if SYNTHESIZE_SINEWAVE_INPUT
			for(unsigned i=0; i<framesPerBuffer; ++i){
				((SAMPLE*)inputBuffer)[i]=sin(phase);
				phase+=synthesizedSinewaveFrequency/SAMPLE_RATE*2*PI;
				if(phase>2*PI) phase-=2*PI;
			}
		#endif
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
