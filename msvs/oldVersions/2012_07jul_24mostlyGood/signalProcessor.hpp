#include <vector>
#include <cmath>

template <class Sample> class SignalProcessor{
	public:
		SignalProcessor(int log2FrameSize, int sampleRate, int oversamplingFactor, int log2fftSize);
		~SignalProcessor();
		void process(const Sample* input, Sample* output);
		void setTempo(float tempo);
		void setBeatsPerMeasure(int);
		void setMeasuresPerLoop(int);
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
		void pitchShift(float amount, const Sample* in, Sample* out);

		int log2FrameSize, sampleRate;
		//pitch shift
		int oversamplingFactor, log2fftSize;
		Sample* gInFIFO;
		Sample* gOutFIFO;
		Sample* gFFTworksp;
		Sample* gLastPhase;
		Sample* gSumPhase;
		Sample* gOutputAccum;
		Sample* gAnaFreq;
		Sample* gAnaMagn;
		Sample* gSynFreq;
		Sample* gSynMagn;
		long gRover;
		Sample PI;
		//loops
		int samplesPerBeat, beatsPerMeasure, measuresPerLoop, sample, beat, measure, loopToRecord, loopsRecorded, bigSample;
		std::vector<Loop<Sample> > loops;
		std::vector<int> loopsToToggle;
};

template <class Sample> SignalProcessor<Sample>::SignalProcessor(
	int log2FrameSize,
	int sampleRate,
	int oversamplingFactor,
	int log2fftSize
):
	log2FrameSize(log2FrameSize), sampleRate(sampleRate),
	oversamplingFactor(oversamplingFactor), log2fftSize(log2fftSize)
{
	//pitch shift
	int fftSize=1<<log2fftSize;
	gInFIFO=new Sample[fftSize];
	gOutFIFO=new Sample[fftSize];
	gFFTworksp=new Sample[2*fftSize];
	gLastPhase=new Sample[fftSize/2+1];
	gSumPhase=new Sample[fftSize/2+1];
	gOutputAccum=new Sample[2*fftSize];
	gAnaFreq=new Sample[fftSize];
	gAnaMagn=new Sample[fftSize];
	gSynFreq=new Sample[fftSize];
	gSynMagn=new Sample[fftSize];
	gRover=0;
	memset(gInFIFO, 0, fftSize*sizeof(Sample));
	memset(gOutFIFO, 0, fftSize*sizeof(Sample));
	memset(gFFTworksp, 0, 2*fftSize*sizeof(Sample));
	memset(gLastPhase, 0, (fftSize/2+1)*sizeof(Sample));
	memset(gSumPhase, 0, (fftSize/2+1)*sizeof(Sample));
	memset(gOutputAccum, 0, 2*fftSize*sizeof(Sample));
	memset(gAnaFreq, 0, fftSize*sizeof(Sample));
	memset(gAnaMagn, 0, fftSize*sizeof(Sample));
	PI=Sample(atan(1.0)*4.0);
	//loops
	samplesPerBeat=0;
	beatsPerMeasure=0;
	loopToRecord=-1;
	loopsRecorded=0;
	loopsToToggle.reserve(32);
	loops.reserve(32);
}

template <class Sample> SignalProcessor<Sample>::~SignalProcessor(){ 
	delete[] gInFIFO;
	delete[] gOutFIFO;
	delete[] gFFTworksp;
	delete[] gLastPhase;
	delete[] gSumPhase;
	delete[] gOutputAccum;
	delete[] gAnaFreq;
	delete[] gAnaMagn;
	delete[] gSynFreq;
	delete[] gSynMagn;
}

template <class Sample> void SignalProcessor<Sample>::process(const Sample* input, Sample* output){
	#if 1
	//pitch shift
	pitchShift(2.0f, input, output);
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
			if(i&bit) j++;
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
	float amount,
	const Sample* in,
	Sample* out
){
	int fftFrameSize=1<<log2fftSize;

	Sample magn, phase, tmp, window, real, imag;
	Sample freqPerBin, expct;
	long i,k, qpd, index, inFifoLatency, stepSize, fftFrameSize2;

	/* set up some handy variables */
	fftFrameSize2 = fftFrameSize/2;
	stepSize = fftFrameSize/oversamplingFactor;
	freqPerBin = sampleRate/(Sample)fftFrameSize;
	expct = 2*PI*(Sample)stepSize/(Sample)fftFrameSize;
	inFifoLatency = fftFrameSize-stepSize;
	if (gRover == 0) gRover = inFifoLatency;

	/* main processing loop */
	for (i = 0; i < (1<<log2FrameSize); i++){

		/* As long as we have not yet collected enough data just read in */
		gInFIFO[gRover] = in[i];
		out[i] = gOutFIFO[gRover-inFifoLatency];
		gRover++;

		/* now we have enough data for processing */
		if (gRover >= fftFrameSize) {
			gRover = inFifoLatency;

			/* do windowing and re,im interleave */
			for (k = 0; k < fftFrameSize;k++) {
				window = Sample(-cos(2*PI*(Sample)k/(Sample)fftFrameSize)/2+Sample(1)/2);
				gFFTworksp[2*k] = float(gInFIFO[k] * window);
				gFFTworksp[2*k+1] = 0.;
			}


			/* ***************** ANALYSIS ******************* */
			/* do transform */
			fft(gFFTworksp, log2fftSize, -1);

			/* this is the analysis step */
			for (k = 0; k <= fftFrameSize2; k++) {

				/* de-interlace FFT buffer */
				real = gFFTworksp[2*k];
				imag = gFFTworksp[2*k+1];

				/* compute magnitude and phase */
				magn = 2*sqrt(real*real + imag*imag);
				phase = atan2(imag,real);

				/* compute phase difference */
				tmp = phase - gLastPhase[k];
				gLastPhase[k] = float(phase);

				/* subtract expected phase difference */
				tmp -= k*expct;

				/* map delta phase into +/- Pi interval */
				qpd = long(tmp/PI);
				if (qpd >= 0) qpd += qpd&1;
				else qpd -= qpd&1;
				tmp -= PI*qpd;

				/* get deviation from bin frequency from the +/- Pi interval */
				tmp = oversamplingFactor*tmp/(2*PI);

				/* compute the k-th partials' true frequency */
				tmp = k*freqPerBin + tmp*freqPerBin;

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
				tmp -= k*freqPerBin;

				/* get bin deviation from freq deviation */
				tmp /= freqPerBin;

				/* take oversamplingFactor into account */
				tmp = 2*PI*tmp/oversamplingFactor;

				/* add the overlap phase advance back in */
				tmp += k*expct;

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
			fft(gFFTworksp, log2fftSize, 1);

			/* do windowing and add to output accumulator */ 
			for(k=0; k < fftFrameSize; k++) {
				window = -cos(2*PI*k/fftFrameSize)/2+Sample(1)/2;
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
