#include "sdlgraphics.hpp"

#include "portaudio.h"
#include "SDL/SDL.h"

#include <cmath>
#include <cstdio>
#include <vector>

using namespace std;

#define DEBUG 0
#define PA_SAMPLE_TYPE paFloat32

const int FRAME_SIZE=64;
const int SAMPLE_RATE=44100;

const int OVERLAP=64;
const float MAX_ERROR=0.01f*OVERLAP;
const int TRANSIENT_FADE_LENGTH=441;
const float PITCH_SHIFT_UP=2.0f;

const float MIN_BSN_FREQ=55.0f;
const float MAX_BSN_FREQ=440.0f;
const float MAX_BSN_PERIOD=SAMPLE_RATE/MIN_BSN_FREQ;
const float MIN_BSN_PERIOD=SAMPLE_RATE/MAX_BSN_FREQ;

#define M_PI 3.14159265358979323846
#define MAX_FRAME_LENGTH 512

typedef float SAMPLE;

#if DEBUG
	static int underflows=0;
#endif

class ChaseBuffer{
	public:
		~ChaseBuffer(){ delete[] buffer; }
		void init(int _size){
			size=_size;
			buffer=new SAMPLE[size];
			i=0;
			o=0;
		}
		SAMPLE take(float increment){
			SAMPLE result=buffer[int(o)];
			o+=increment;
			if(int(o)>=size) o-=size;
			return result;
		}
		void put(SAMPLE s){
			buffer[i]=s;
			++i;
			i%=size;
			#if DEBUG
				if(i==int(o)) printf("overflow\n");
			#endif
		}
		void skipAndCrossfade(int length){
			for(int j=0; j<length; ++j)
				buffer[(i-j+size)%size]=(buffer[(i-j+size)%size]*(length-j)+buffer[(int(o)+length-j+size)%size]*j)/length;
			o=float((i-(length-1)+size)%size);
		}
		void back(int length){
			o-=length;
			if(o<0) o+=size;
		}
		SAMPLE recentTakePutSimilarity(int length){
			SAMPLE result=0;
			for(int j=0; j<length; ++j)
				result+=abs(buffer[(i-j+size)%size]-buffer[(int(o)+length-j+size)%size]);
			return result;
		}
		SAMPLE recentPutSimilarity(int k, int length){
			SAMPLE result=0;
			for(int j=0; j<length; ++j)
				result+=abs(buffer[(i-j+size)%size]-buffer[(k-j+size)%size]);
			return result;
		}
		int space(){ return (i-int(o)+size)%size; }
		int spaceFrom(int k){ return (i-k+size)%size; }
		int negativeSpace(){ return (int(o)-i+size)%size; }
		int length(int from, int to){ return (to-from+size)%size; }
		int& putIndex(){ return i; }
		float& takeIndex(){ return o; }
		bool putIndexIsBetween(int start, int end){
			if(start<end){
				if(start>i) return false;
				if(end<i) return false;
				return true;
			}
			else{
				if(start<=i) return true;
				if(end>=i) return true;
				return false;
			}
		}
	private:
		SAMPLE* buffer;
		int size, i;
		float o;
};

class Buffer{
	public:
		Buffer(int s){
			size=s;
			samples=new SAMPLE[size];
		}
		~Buffer(){ delete[] samples; }
		SAMPLE& at(int i){ return samples[i]; }
	private:
		int size;
		SAMPLE* samples;
};

struct Loop{
	Loop(): buffer(NULL), active(false) {}
	Buffer* buffer;
	string name;
	bool active;
};

void fft(float* signal, int log2size, int sign){
	int size=1<<log2size;
	for(int i=2; i<2*size-2; i+=2){
		int j=0;
		for(int bit=2; bit<2*size; bit<<=1){
			if(i&bit) j++;
			j<<=1;
		}
		if(i<j){
			float temp=signal[i];
			signal[i]=signal[j];
			signal[j]=temp;
			temp=signal[i+1];
			signal[i+1]=signal[j+1];
			signal[j+1]=temp;
		}
	}
	int le=2;
	for(int i=0; i<log2size; i++){
		le<<=1;
		float ur=1.0;
		float ui=0.0;
		float arg=float(M_PI/(le>>2));
		float wr=cos(arg);
		float wi=sign*sin(arg);
		for(int j=0; j<le>>1; j+=2){
			int a=j;
			int b=j+(le>>1);
			for(int k=j; k<2*size; k+=le){
				float tr=signal[b]*ur-signal[b+1]*ui;
				float ti=signal[b]*ui+signal[b+1]*ur;
				signal[b]=signal[a]-tr;
				signal[b+1]=signal[a+1]-ti;
				signal[a]+=tr;
				signal[a+1]+=ti;
				a+=le;
				b+=le;
			}
			float temp=ur*wr-ui*wi;
			ui=ur*wi+ui*wr;
			ur=temp;
		}
	}
}

void pitchShift(
	float amount,
	int numSampsToProcess,
	int log2fftFrameSize,
	int oversamplingFactor,
	float sampleRate,
	const float* in,
	float* out
){
	int fftFrameSize=1<<log2fftFrameSize;

	static float gInFIFO[MAX_FRAME_LENGTH];
	static float gOutFIFO[MAX_FRAME_LENGTH];
	static float gFFTworksp[2*MAX_FRAME_LENGTH];
	static float gLastPhase[MAX_FRAME_LENGTH/2+1];
	static float gSumPhase[MAX_FRAME_LENGTH/2+1];
	static float gOutputAccum[2*MAX_FRAME_LENGTH];
	static float gAnaFreq[MAX_FRAME_LENGTH];
	static float gAnaMagn[MAX_FRAME_LENGTH];
	static float gSynFreq[MAX_FRAME_LENGTH];
	static float gSynMagn[MAX_FRAME_LENGTH];
	static long gRover = false, gInit = false;
	double magn, phase, tmp, window, real, imag;
	double freqPerBin, expct;
	long i,k, qpd, index, inFifoLatency, stepSize, fftFrameSize2;

	/* set up some handy variables */
	fftFrameSize2 = fftFrameSize/2;
	stepSize = fftFrameSize/oversamplingFactor;
	freqPerBin = sampleRate/(double)fftFrameSize;
	expct = 2.*M_PI*(double)stepSize/(double)fftFrameSize;
	inFifoLatency = fftFrameSize-stepSize;
	if (gRover == false) gRover = inFifoLatency;

	/* initialize our static arrays */
	if (gInit == false) {
		memset(gInFIFO, 0, MAX_FRAME_LENGTH*sizeof(float));
		memset(gOutFIFO, 0, MAX_FRAME_LENGTH*sizeof(float));
		memset(gFFTworksp, 0, 2*MAX_FRAME_LENGTH*sizeof(float));
		memset(gLastPhase, 0, (MAX_FRAME_LENGTH/2+1)*sizeof(float));
		memset(gSumPhase, 0, (MAX_FRAME_LENGTH/2+1)*sizeof(float));
		memset(gOutputAccum, 0, 2*MAX_FRAME_LENGTH*sizeof(float));
		memset(gAnaFreq, 0, MAX_FRAME_LENGTH*sizeof(float));
		memset(gAnaMagn, 0, MAX_FRAME_LENGTH*sizeof(float));
		gInit = true;
	}

	/* main processing loop */
	for (i = 0; i < numSampsToProcess; i++){

		/* As long as we have not yet collected enough data just read in */
		gInFIFO[gRover] = in[i];
		out[i] = gOutFIFO[gRover-inFifoLatency];
		gRover++;

		/* now we have enough data for processing */
		if (gRover >= fftFrameSize) {
			gRover = inFifoLatency;

			/* do windowing and re,im interleave */
			for (k = 0; k < fftFrameSize;k++) {
				window = float(-.5*cos(2.*M_PI*(double)k/(double)fftFrameSize)+.5);
				gFFTworksp[2*k] = float(gInFIFO[k] * window);
				gFFTworksp[2*k+1] = 0.;
			}


			/* ***************** ANALYSIS ******************* */
			/* do transform */
			fft(gFFTworksp, log2fftFrameSize, -1);

			/* this is the analysis step */
			for (k = 0; k <= fftFrameSize2; k++) {

				/* de-interlace FFT buffer */
				real = gFFTworksp[2*k];
				imag = gFFTworksp[2*k+1];

				/* compute magnitude and phase */
				magn = 2.*sqrt(real*real + imag*imag);
				phase = atan2(imag,real);

				/* compute phase difference */
				tmp = phase - gLastPhase[k];
				gLastPhase[k] = float(phase);

				/* subtract expected phase difference */
				tmp -= (double)k*expct;

				/* map delta phase into +/- Pi interval */
				qpd = long(tmp/M_PI);
				if (qpd >= 0) qpd += qpd&1;
				else qpd -= qpd&1;
				tmp -= M_PI*(double)qpd;

				/* get deviation from bin frequency from the +/- Pi interval */
				tmp = oversamplingFactor*tmp/(2.*M_PI);

				/* compute the k-th partials' true frequency */
				tmp = (double)k*freqPerBin + tmp*freqPerBin;

				/* store magnitude and true frequency in analysis arrays */
				gAnaMagn[k] = float(magn);
				gAnaFreq[k] = float(tmp);

			}

			/* ***************** PROCESSING ******************* */
			/* this does the actual pitch shifting */
			memset(gSynMagn, 0, fftFrameSize*sizeof(float));
			memset(gSynFreq, 0, fftFrameSize*sizeof(float));
			for (k = 0; k <= fftFrameSize2; k++) { 
				index = long(k*amount);
				if (index <= fftFrameSize2) { 
					gSynMagn[index] += gAnaMagn[k]; 
					gSynFreq[index] = gAnaFreq[k] * amount; 
				} 
			}
			
			/* ***************** SYNTHESIS ******************* */
			/* this is the synthesis step */
			for (k = 0; k <= fftFrameSize2; k++) {

				/* get magnitude and true frequency from synthesis arrays */
				magn = gSynMagn[k];
				tmp = gSynFreq[k];

				/* subtract bin mid frequency */
				tmp -= (double)k*freqPerBin;

				/* get bin deviation from freq deviation */
				tmp /= freqPerBin;

				/* take oversamplingFactor into account */
				tmp = 2.*M_PI*tmp/oversamplingFactor;

				/* add the overlap phase advance back in */
				tmp += (double)k*expct;

				/* accumulate delta phase to get bin phase */
				gSumPhase[k] += float(tmp);
				phase = gSumPhase[k];

				/* get real and imag part and re-interleave */
				gFFTworksp[2*k] = float(magn*cos(phase));
				gFFTworksp[2*k+1] = float(magn*sin(phase));
			} 

			/* zero negative frequencies */
			for (k = fftFrameSize+2; k < 2*fftFrameSize; k++) gFFTworksp[k] = 0.;

			/* do inverse transform */
			fft(gFFTworksp, log2fftFrameSize, 1);

			/* do windowing and add to output accumulator */ 
			for(k=0; k < fftFrameSize; k++) {
				window = -.5*cos(2.*M_PI*(double)k/(double)fftFrameSize)+.5;
				gOutputAccum[k] += float(2.*window*gFFTworksp[2*k]/(fftFrameSize2*oversamplingFactor));
			}
			for (k = 0; k < stepSize; k++) gOutFIFO[k] = gOutputAccum[k];

			/* shift accumulator */
			memmove(gOutputAccum, gOutputAccum+stepSize, fftFrameSize*sizeof(float));

			/* move input FIFO */
			for (k = 0; k < inFifoLatency; k++) gInFIFO[k] = gInFIFO[k+stepSize];
		}
	}
}

class SignalProcessor{
	public:
		SignalProcessor(int frameSize);
		~SignalProcessor();
		void process(const SAMPLE* input, SAMPLE* output);
		void setTempo(float tempo);
		void setBeatsPerMeasure(int);
		void setMeasuresPerLoop(int);
		float normalizedTimeToNextBeat();
		int readBeat();
		int readMeasure();
		bool lastMeasure();
		string* addLoop();
		int numLoops(){ return loops.size(); }
		Loop* getLoop(int i){ return &loops[i]; }
		void toggleLoop(int i);
		int loopRecording(){ return loopToRecord; }
	private:
		int frameSize;
		/*pitch shift*/
		
		/*pitch shift down*/
		ChaseBuffer chaseBuffer;
		/*loops*/
		int samplesPerBeat, beatsPerMeasure, measuresPerLoop, sample, beat, measure, loopToRecord, loopsRecorded, bigSample;
		vector<Loop> loops;
		vector<int> loopsToToggle;
};

SignalProcessor::SignalProcessor(int frameSize):
	frameSize(frameSize)
{
	//pitch shift

	//pitch shift down
	chaseBuffer.init(int(MAX_BSN_PERIOD)*4);
	//loops
	samplesPerBeat=0;
	beatsPerMeasure=0;
	loopToRecord=-1;
	loopsRecorded=0;
	loopsToToggle.reserve(32);
	loops.reserve(32);
}

SignalProcessor::~SignalProcessor(){}

void SignalProcessor::process(const SAMPLE* input, SAMPLE* output){
	#if 1
	/*pitch shift*/
	pitchShift(2.0f, FRAME_SIZE, 9, 4, 44100.0f, input, output);
	#endif
	for(int i=0; i<frameSize; ++i){
		#if 0
		/*pitch shift down*/
		//put
		chaseBuffer.put(input[i]);
		//take
		output[i]=chaseBuffer.take(0.5f);
		//attempt to skip
		if(chaseBuffer.space()>int(MIN_BSN_PERIOD)&&chaseBuffer.recentTakePutSimilarity(OVERLAP)<MAX_ERROR)
			chaseBuffer.skipAndCrossfade(OVERLAP);
		//force skip
		if(chaseBuffer.negativeSpace()<TRANSIENT_FADE_LENGTH)
			chaseBuffer.skipAndCrossfade(TRANSIENT_FADE_LENGTH);
		#endif
		#if 0
		/*loops*/
		//play
		for(int j=0; j<loopsRecorded; ++j)
			if(loops[j].active) output[i]+=loops[j].buffer->at(bigSample);
		//record
		if(loopToRecord>=0)
			loops[loopToRecord].buffer->at(bigSample)=input[i];
		++sample;
		++bigSample;
		if(sample==samplesPerBeat){
			sample=0;
			++beat;
			if(beat==beatsPerMeasure){
				beat=0;
				++measure;
				if(measure==measuresPerLoop){
					measure=0;
					bigSample=0;
					if((int)loops.size()>loopsRecorded){
						loopToRecord=loopsRecorded;
						++loopsRecorded;
					}
					else loopToRecord=-1;
					for(unsigned j=0; j<loopsToToggle.size(); ++j)
						loops[loopsToToggle[j]].active=!loops[loopsToToggle[j]].active;
					loopsToToggle.clear();
				}
			}
		}
		#endif
	}
}

void SignalProcessor::setTempo(float t){
	samplesPerBeat=int(SAMPLE_RATE*60/t);
	sample=0;
}

void SignalProcessor::setBeatsPerMeasure(int b){
	beatsPerMeasure=b;
	beat=0;
}

void SignalProcessor::setMeasuresPerLoop(int m){
	measuresPerLoop=m;
	measure=0;
}

float SignalProcessor::normalizedTimeToNextBeat(){
	return float(samplesPerBeat-sample)/samplesPerBeat;
}

int SignalProcessor::readBeat(){
	return beat;
}

int SignalProcessor::readMeasure(){
	return measure;
}

bool SignalProcessor::lastMeasure(){
	return measure==measuresPerLoop-1;
}

string* SignalProcessor::addLoop(){
	loops.resize(loops.size()+1);
	loops.back().buffer=new Buffer(samplesPerBeat*beatsPerMeasure*measuresPerLoop);
	return &loops.back().name;
}

void SignalProcessor::toggleLoop(int i){
	loopsToToggle.push_back(i);
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
		#if 0
			for(unsigned i=0; i<framesPerBuffer; ++i)
				((SAMPLE*)outputBuffer)[i]=((SAMPLE*)inputBuffer)[i];
		#else
			((SignalProcessor*) userData)->process((SAMPLE*) inputBuffer, (SAMPLE*) outputBuffer);
		#endif
	}
	return paContinue;
}

void error(const PaError& err){
	Pa_Terminate();
	fprintf(stderr, "An error occured while using the portaudio stream\n");
	fprintf(stderr, "Error number: %d\n", err);
	fprintf(stderr, "Error message: %s\n", Pa_GetErrorText(err));
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
	printf("Started.\n");
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
								output=signalProcessor.addLoop();
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
			/*beat*/
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
			/*loops*/
			for(int i=0; i<signalProcessor.numLoops(); ++i){
				rect.x=size*19*(i%3)+size*5;
				rect.y=size*4*(i/3)+size;
				rect.w=size*18;
				rect.h=size*3;
				if(signalProcessor.getLoop(i)->active)
					SDL_FillRect(screen, &rect, SDL_MapRGB(screen->format, 0x7f, 0x0f, 0x7f));
				else
					SDL_FillRect(screen, &rect, SDL_MapRGB(screen->format, 0x3f, 0x3f, 0x3f));
				outchar(rect.x+size, rect.y+size, SDL_MapRGB(screen->format, 0xff, 0xff, 0xff), i+'a', screen, size);
				outtext(rect.x+size*5, rect.y+size, SDL_MapRGB(screen->format, 0, 0xff, 0), signalProcessor.getLoop(i)->name, screen, size);
			}
			rect.x=size*19*(signalProcessor.loopRecording()%3)+size*5;
			rect.y=size*4*(signalProcessor.loopRecording()/3)+size;
			rect.w=size;
			rect.h=size;
			SDL_FillRect(screen, &rect, SDL_MapRGB(screen->format, 0xff, 0, 0));
			/*input*/
			outtext(8, screen->h-8-size, SDL_MapRGB(screen->format, 0xff, 0xff, 0xff), input, screen, size);
			/*finish*/
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
	printf("Finished.\n");
	#if DEBUG
		printf("Underflows: %d\n", underflows);
	#endif
	Pa_Terminate();
	//finish
	SDL_Quit();
	return 0;
}
