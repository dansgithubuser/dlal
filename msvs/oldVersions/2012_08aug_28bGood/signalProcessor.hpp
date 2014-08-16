#include <vector>
#include <cmath>

template <class Sample> class SignalProcessor{
	public:
		SignalProcessor(int log2FrameSize, int sampleRate, int overlapFactor, int log2FftSize);
		~SignalProcessor();
		void process(const Sample* input, Sample* output);
		void setTempo(float tempo);
		void setBeatsPerMeasure(int);
		void setMeasuresPerLoop(int);
		void setPitches(std::vector<std::pair<float, float> >);
		float normalizedTimeToNextBeat();
		int readBeat();
		int readMeasure();
		bool lastMeasure();
		std::string& addLoop();
		int numLoops(){ return loops.size(); }
		std::string nameOfLoop(int i){ return loops[i].name; }
		bool loopIsActive(int i){ return loops[i].active; }
		void toggleLoop(int i);
		int loopRecording(){ return loopToRecord; }
	private:
		
		template <class Sample> class Buffer{
			public:
				Buffer(int s){
					size=s;
					samples=new Sample[size];
				}
				~Buffer(){ delete[] samples; }
				Sample& at(int i){ return samples[i]; }
			private:
				int size;
				Sample* samples;
		};

		template <class Sample> struct Loop{
			Loop(): buffer(NULL), active(false) {}
			Buffer<Sample>* buffer;
			std::string name;
			bool active;
		};

		void fft(Sample* signal, int log2size, int sign);
		void pitchShift(const Sample* input, Sample* output);

		int log2FrameSize, sampleRate;
		//pitch shift
		Sample PI;
		int overlapFactor, log2FftSize, samplesPerFft, inputIndex, outputIndex;
		Sample freqPerBin;
		Sample* inputHistory;
		Sample* outputHistory;
		Sample* fftSignal;
		Sample* previousPhase;
		std::vector<Sample*> outputPhase;
		Sample* inputFrequency;
		Sample* inputMagnitude;
		Sample* outputFrequency;
		Sample* outputMagnitude;
		Sample* unwindowedOutput;
		std::vector<std::pair<float, float> > pitches;
		//loops
		int samplesPerBeat, beatsPerMeasure, measuresPerLoop, sample, beat, measure, loopToRecord, loopsRecorded, bigSample;
		std::vector<Loop<Sample> > loops;
		std::vector<int> loopsToToggle;
};

template <class Sample> SignalProcessor<Sample>::SignalProcessor(
	int log2FrameSize,
	int sampleRate,
	int overlapFactor,
	int log2FftSize
):
	log2FrameSize(log2FrameSize), sampleRate(sampleRate),
	overlapFactor(overlapFactor), log2FftSize(log2FftSize)
{
	//pitch shift
	PI=Sample(atan(1.0)*4.0);
	samplesPerFft=(1<<log2FftSize)/overlapFactor;
	inputIndex=0;
	outputIndex=0;
	freqPerBin=sampleRate/(Sample)(1<<log2FftSize);
	inputHistory=new Sample[1<<log2FftSize];
	outputHistory=new Sample[(1<<log2FftSize)+samplesPerFft];
	fftSignal=new Sample[1<<(log2FftSize+1)];
	previousPhase=new Sample[(1<<(log2FftSize-1))+1];
	inputFrequency=new Sample[1<<log2FftSize];
	inputMagnitude=new Sample[1<<log2FftSize];
	outputFrequency=new Sample[1<<log2FftSize];
	outputMagnitude=new Sample[1<<log2FftSize];
	unwindowedOutput=new Sample[1<<log2FftSize];
	for(int i=0; i<(1<<log2FftSize); ++i) inputHistory[i]=0;
	for(int i=0; i<(1<<log2FftSize)+samplesPerFft; ++i) outputHistory[i]=0;
	for(int i=0; i<(1<<(log2FftSize-1))+1; ++i) previousPhase[i]=0;
	//loops
	samplesPerBeat=0;
	beatsPerMeasure=0;
	loopToRecord=-1;
	loopsRecorded=0;
	loopsToToggle.reserve(32);
	loops.reserve(32);
}

template <class Sample> SignalProcessor<Sample>::~SignalProcessor(){ 
	delete[] inputHistory;
	delete[] outputHistory;
	delete[] fftSignal;
	delete[] previousPhase;
	for(unsigned i=0; i<outputPhase.size(); ++i) delete[] outputPhase[i];
	delete[] inputFrequency;
	delete[] inputMagnitude;
	delete[] outputFrequency;
	delete[] outputMagnitude;
	delete[] unwindowedOutput;
}

template <class Sample> void SignalProcessor<Sample>::process(const Sample* input, Sample* output){
	#if 1
	//pitch shift
	if(pitches.size()) pitchShift(input, output);
	#endif
	for(int i=0; i<(1<<log2FrameSize); ++i){
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

template <class Sample> void SignalProcessor<Sample>::setTempo(float t){
	samplesPerBeat=int(sampleRate*60/t);
	sample=0;
}

template <class Sample> void SignalProcessor<Sample>::setBeatsPerMeasure(int b){
	beatsPerMeasure=b;
	beat=0;
}

template <class Sample> void SignalProcessor<Sample>::setMeasuresPerLoop(int m){
	measuresPerLoop=m;
	measure=0;
}

template <class Sample> void SignalProcessor<Sample>::setPitches(std::vector<std::pair<float, float> > p){
	for(unsigned i=0; i<p.size(); ++i){
		if(i<pitches.size()) pitches[i]=p[i];
		else{
			outputPhase.push_back(new Sample[(1<<(log2FftSize-1))+1]);
			for(int j=0; j<(1<<(log2FftSize-1))+1; ++j) outputPhase[i][j]=0;
			pitches.push_back(p[i]);
		}
	}
	for(unsigned i=p.size(); i<pitches.size(); ++i) pitches[i]=std::pair<float, float>(0.0f, 0.0f);
}

template <class Sample> float SignalProcessor<Sample>::normalizedTimeToNextBeat(){
	return float(samplesPerBeat-sample)/samplesPerBeat;
}

template <class Sample> int SignalProcessor<Sample>::readBeat(){
	return beat;
}

template <class Sample> int SignalProcessor<Sample>::readMeasure(){
	return measure;
}

template <class Sample> bool SignalProcessor<Sample>::lastMeasure(){
	return measure==measuresPerLoop-1;
}

template <class Sample> std::string& SignalProcessor<Sample>::addLoop(){
	loops.resize(loops.size()+1);
	loops.back().buffer=new Buffer<Sample>(samplesPerBeat*beatsPerMeasure*measuresPerLoop);
	return loops.back().name;
}

template <class Sample> void SignalProcessor<Sample>::toggleLoop(int i){
	loopsToToggle.push_back(i);
}

template <class Sample> void SignalProcessor<Sample>::fft(Sample* signal, int log2size, int sign){
	int size=1<<log2size;
	for(int i=2; i<2*size-2; i+=2){
		int j=0;
		for(int bit=2; bit<2*size; bit<<=1){
			if(i&bit) ++j;
			j<<=1;
		}
		if(i<j){
			Sample temp=signal[i];
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
		Sample ur=1.0;
		Sample ui=0.0;
		Sample arg=Sample(PI/(le>>2));
		Sample wr=cos(arg);
		Sample wi=sign*sin(arg);
		for(int j=0; j<le>>1; j+=2){
			int a=j;
			int b=j+(le>>1);
			for(int k=j; k<2*size; k+=le){
				Sample tr=signal[b]*ur-signal[b+1]*ui;
				Sample ti=signal[b]*ui+signal[b+1]*ur;
				signal[b]=signal[a]-tr;
				signal[b+1]=signal[a+1]-ti;
				signal[a]+=tr;
				signal[a+1]+=ti;
				a+=le;
				b+=le;
			}
			Sample temp=ur*wr-ui*wi;
			ui=ur*wi+ui*wr;
			ur=temp;
		}
	}
}

template <class Sample> void SignalProcessor<Sample>::pitchShift(
	const Sample* input,
	Sample* output
){
	//read input and write output
	for(int i=0; i<(1<<log2FrameSize); ++i){
		inputHistory[inputIndex+i]=input[i];
		output[i]=outputHistory[outputIndex+i];
	}
	inputIndex+=(1<<log2FrameSize);
	if(inputIndex==(1<<log2FftSize)) inputIndex=0;
	outputIndex+=(1<<log2FrameSize);
	if(outputIndex==samplesPerFft){//if it's time to do an stft
		outputIndex=0;
		//windowing and interleaving
		for(int j=0; j<(1<<log2FftSize); ++j){
			Sample window=Sample(-cos(2*PI*j/(1<<log2FftSize))/2)+Sample(1)/2;
			fftSignal[2*j]=inputHistory[(inputIndex+j)%(1<<log2FftSize)]*window;
			fftSignal[2*j+1]=0;
		}
		//transform
		fft(fftSignal, log2FftSize, -1);
		for(int k=0; k<=(1<<(log2FftSize-1)); ++k){
			Sample a=fftSignal[2*k];//real
			Sample b=fftSignal[2*k+1];//imaginary
			Sample magnitude=2*sqrt(a*a+b*b);
			Sample phase=atan2(b, a);
			Sample dPhase=phase-previousPhase[k];
			previousPhase[k]=phase;
			//subtract expected phase difference
			dPhase-=k*2*PI/overlapFactor;
			//map delta phase into +/- pi interval
			dPhase-=2*PI*floor((dPhase+PI)/(2*PI));
			//store magnitude and true frequency in analysis arrays
			inputMagnitude[k]=magnitude;
			inputFrequency[k]=k*freqPerBin+freqPerBin*overlapFactor*dPhase/(2*PI);
		}
		for(int i=0; i<(1<<log2FftSize); ++i) unwindowedOutput[i]=0;
		for(unsigned pitchIndex=0; pitchIndex<pitches.size(); ++pitchIndex){
			//pitch shift
			for(int i=0; i<(1<<(log2FftSize-1)); ++i) outputMagnitude[i]=0;
			for(int k=0; k<=(1<<(log2FftSize-1)); ++k){
				int j=int(k*pitches[pitchIndex].first);
				if(j<=(1<<(log2FftSize-1))){
					outputMagnitude[j]+=inputMagnitude[k];
					outputFrequency[j]=inputFrequency[k]*pitches[pitchIndex].first;
				}
			}
			//transform back
			for(int k=0; k<=(1<<(log2FftSize-1)); ++k){
				//get magnitude and true frequency from synthesis arrays
				Sample magnitude=outputMagnitude[k];
				Sample dPhase=(outputFrequency[k]/freqPerBin-k)*2*PI/overlapFactor;
				//put expected phase difference back
				dPhase+=k*2*PI/overlapFactor;
				//add delta phase to get current phase
				outputPhase[pitchIndex][k]+=dPhase;
				//get real and imaginary parts and reinterleave
				fftSignal[2*k]=magnitude*Sample(cos(outputPhase[pitchIndex][k]));
				fftSignal[2*k+1]=magnitude*Sample(sin(outputPhase[pitchIndex][k]));
			}
			//zero negative frequencies
			for(int k=(1<<log2FftSize)+2; k<(1<<(log2FftSize+1)); ++k) fftSignal[k]=0;
			//do inverse transform
			fft(fftSignal, log2FftSize, 1);
			for(int i=0; i<(1<<log2FftSize); ++i) unwindowedOutput[i]+=pitches[pitchIndex].second*fftSignal[2*i];
		}
		//do windowing and add to output
		for(int k=0; k<(1<<log2FftSize); ++k){
			Sample window=-cos(2*PI*k/(1<<log2FftSize))/2+Sample(1)/2;
			outputHistory[k]=outputHistory[k+samplesPerFft]+2*window*unwindowedOutput[k]/((1<<(log2FftSize-1))*overlapFactor);
		}
	}
}
