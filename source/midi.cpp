#include "midi.hpp"

#include "RtMidi.h"

static RtMidiIn* fRtMidiIn=nullptr;
static std::function<void(std::vector<unsigned char>)> fCallback;

static void rtMidiCallback(double delta, std::vector<unsigned char>* message, void* userData){
	fCallback(*message);
}

namespace dlal{

void midiInit(std::function<void(std::vector<unsigned char>&)> callback){
	fCallback=callback;
	try{
		fRtMidiIn=new RtMidiIn();
	}
	catch(RtMidiError& error){
		error.printMessage();
		return;
	}
	if(fRtMidiIn->getPortCount()<1) return;
	fRtMidiIn->openPort(0);
	fRtMidiIn->setCallback(rtMidiCallback);
}

void midiFinish(){
	delete fRtMidiIn;
}

}//namespace dlal
