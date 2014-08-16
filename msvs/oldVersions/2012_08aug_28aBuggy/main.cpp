#include "signalProcessor.hpp"

#include "sdlgraphics.hpp"

#include "portaudio.h"
#include "SDL/SDL.h"

#include <iostream>

using namespace std;

#define DEBUG 1

typedef float SAMPLE;

static const PaSampleFormat PA_SAMPLE_TYPE=paFloat32;
static const int LOG2_FRAME_SIZE=6;
static const int SAMPLE_RATE=44100;

#if DEBUG
	static int underflows=0;
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
		#if 0
			for(unsigned i=0; i<framesPerBuffer; ++i)
				((SAMPLE*)outputBuffer)[i]=((SAMPLE*)inputBuffer)[i];
		#else
			((SignalProcessor<SAMPLE>*) userData)->process((SAMPLE*) inputBuffer, (SAMPLE*) outputBuffer);
		#endif
	}
	return paContinue;
}

void error(const PaError& err){
	Pa_Terminate();
	cerr<<"An error occured while using the portaudio stream\n";
	cerr<<"Error number: "<<err<<"\n";
	cerr<<"Error message: "<<Pa_GetErrorText(err)<<"\n";
}

int main(int argc, char** argv){
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
		cerr<<"Error: No default input device.\n";
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
		cerr<<"Error: No default output device.\n";
		error(err);
		return -1;
	}
	outputParameters.channelCount=1;
	outputParameters.sampleFormat=PA_SAMPLE_TYPE;
	outputParameters.suggestedLatency=Pa_GetDeviceInfo(outputParameters.device)->defaultLowOutputLatency;
	outputParameters.hostApiSpecificStreamInfo=NULL;
	//signal processor
	SignalProcessor<SAMPLE> signalProcessor(LOG2_FRAME_SIZE, SAMPLE_RATE, 4, 9);
	vector<float> pitches;///
	//pitches.push_back(1.25f);
	//pitches.push_back(1.0f);
	//pitches.push_back(1.5f);
	pitches.push_back(2.0f);
	signalProcessor.setPitches(pitches);
	//open stream
	err=Pa_OpenStream(
		&stream,
		&inputParameters,
		&outputParameters,
		SAMPLE_RATE,
		1<<LOG2_FRAME_SIZE,
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
	cout<<"Started.\n";
	//SDL initialization
	SDL_Init(SDL_INIT_EVERYTHING);
	SDL_Surface* screen=SDL_SetVideoMode(640, 480, 32, SDL_SWSURFACE);
	//interface event loop
	bool quit=false, haveFirstBeat=false, settingBeatsPerMeasure=false, settingMeasuresPerLoop=false, togglingLoop=false;
	int firstBeatTime, redrawPhase=0;
	string input;
	string* output=NULL;
	while(!quit){
		SDL_Event sdlEvent;
		while(SDL_PollEvent(&sdlEvent)){
			if(SDL_GetModState()&KMOD_CTRL)
				switch(sdlEvent.type){
					case SDL_KEYDOWN:
						switch(sdlEvent.key.keysym.sym){
							case 'q': quit=true; break;
							default: break;
						}
						break;
					default: break;
				}
			else
				switch(sdlEvent.type){
					case SDL_KEYDOWN:
						if(output){
							switch(sdlEvent.key.keysym.sym){
								case SDLK_BACKSPACE: if(input.size()) input.erase(input.end()-1); break;
								case SDLK_RETURN:
									*output=input;
									output=NULL;
									input="";
									break;
								default: input+=sdlEvent.key.keysym.sym;
							}
							break;
						}
						else if(sdlEvent.key.keysym.sym>='0'&&sdlEvent.key.keysym.sym<='9'){
							if(settingBeatsPerMeasure){
								signalProcessor.setBeatsPerMeasure(sdlEvent.key.keysym.sym-'0');
								settingBeatsPerMeasure=false;
							}
							else if(settingMeasuresPerLoop){
								signalProcessor.setMeasuresPerLoop(sdlEvent.key.keysym.sym-'0');
								settingMeasuresPerLoop=false;
							}
						}
						else if(togglingLoop){
							signalProcessor.toggleLoop(sdlEvent.key.keysym.sym-'a');
							togglingLoop=false;
							break;
						}
						switch(sdlEvent.key.keysym.sym){
							case 'a': togglingLoop=true; break;
							case 'b': settingBeatsPerMeasure=true; break;
							case 'm': settingMeasuresPerLoop=true; break;
							case 'r':
								output=&signalProcessor.addLoop();
								break;
							case 't':{
								if(!haveFirstBeat||SDL_GetTicks()-firstBeatTime>2000){
									firstBeatTime=SDL_GetTicks();
									haveFirstBeat=true;
								}
								else{
									signalProcessor.setTempo(60000.0f/(SDL_GetTicks()-firstBeatTime));
									haveFirstBeat=false;
								}
								break;
							}
							default: break;
						}
						break;
					default: break;
				}
		}
		SDL_Delay(1);
		++redrawPhase;
		if(redrawPhase>=20){
			SDL_FillRect(screen, NULL, SDL_MapRGB(screen->format, 0, 0, 0));
			int size=min(screen->w/60, screen->h/60);
			//beat
			float amplitude=signalProcessor.normalizedTimeToNextBeat();
			SDL_Rect rect;
			rect.x=0;
			rect.y=0;
			rect.w=size*4;
			rect.h=size*4;
			if(signalProcessor.readBeat()==0){
				SDL_FillRect(
					screen,
					&rect,
					SDL_MapRGB(screen->format, Uint8(255*amplitude), 0, 0));
			}
			else if(signalProcessor.lastMeasure()){
				SDL_FillRect(
					screen,
					&rect,
					SDL_MapRGB(screen->format, 0, 0, Uint8(255*amplitude)));
			}
			else{
				SDL_FillRect(
					screen,
					&rect,
					SDL_MapRGB(screen->format, Uint8(255*amplitude), Uint8(255*amplitude), Uint8(255*amplitude)));
			}
			//loops
			for(int i=0; i<signalProcessor.numLoops(); ++i){
				rect.x=size*19*(i%3)+size*5;
				rect.y=size*4*(i/3)+size;
				rect.w=size*18;
				rect.h=size*3;
				if(signalProcessor.loopIsActive(i))
					SDL_FillRect(screen, &rect, SDL_MapRGB(screen->format, 0x7f, 0x0f, 0x7f));
				else
					SDL_FillRect(screen, &rect, SDL_MapRGB(screen->format, 0x3f, 0x3f, 0x3f));
				outchar(rect.x+size, rect.y+size, SDL_MapRGB(screen->format, 0xff, 0xff, 0xff), i+'a', screen, size);
				outtext(rect.x+size*5, rect.y+size, SDL_MapRGB(screen->format, 0, 0xff, 0), signalProcessor.nameOfLoop(i), screen, size);
			}
			rect.x=size*19*(signalProcessor.loopRecording()%3)+size*5;
			rect.y=size*4*(signalProcessor.loopRecording()/3)+size;
			rect.w=size;
			rect.h=size;
			SDL_FillRect(screen, &rect, SDL_MapRGB(screen->format, 0xff, 0, 0));
			//input
			outtext(8, screen->h-8-size, SDL_MapRGB(screen->format, 0xff, 0xff, 0xff), input, screen, size);
			//finish
			redrawPhase=0;
			SDL_Flip(screen);
		}
	}
	//stop
	err=Pa_CloseStream(stream);
	if(err!=paNoError){
		error(err);
		return -1;
	}
	cout<<"Finished.\n";
	#if DEBUG
		cout<<"Underflows: "<<underflows<<"\n";
	#endif
	Pa_Terminate();
	//finish
	SDL_Quit();
	return 0;
}
