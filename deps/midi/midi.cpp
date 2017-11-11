#include "midi.hpp"

#include <algorithm>
#include <cstring>
#include <fstream>
#include <map>
#include <stdexcept>

#include <obvious.hpp>

namespace dlal{

static const unsigned TRACK_HEADER_SIZE=8;
static const std::string TRACK_TITLE="MTrk";
static const unsigned HEADER_SIZE=14;
static const std::string HEADER_TITLE="MThd";

//Return the bytes that specify a delta time equal to ticks.
static Bytes writeDelta(int ticks){
	Bytes result;
	for(unsigned i=0; i<4; ++i){
		int byte=ticks&0x7f;
		ticks=ticks>>7;
		result.insert(result.begin(), byte);
		if(ticks==0){
			for(unsigned j=0; j<result.size()-1; ++j) result[j]|=0x80;
			return result;
		}
	}
	throw std::runtime_error("delta too big");
}

//Return delta that starts at bytes[i].
//i will be overwritten with the index just after the end of the delta.
static int readDelta(const Bytes& bytes, unsigned& i){
	int result=0;
	for(int j=0; j<4||toss("delta too big"); ++j){
		result<<=7;
		result+=bytes.at(i)&0x7f;
		++i;
		if(!(bytes.at(i-1)&0x80)) break;
	}
	return result;
}

//Return the pairs in trackChunk in a list.
//trackChunk is assumed to have come from a track produced by chunkitize.
static std::vector<Midi::Pair> getPairs(const Bytes& trackChunk){
	std::vector<Midi::Pair> pairs;
	unsigned i=TRACK_HEADER_SIZE;
	uint8_t status=0;
	while(i<trackChunk.size()){
		auto delta=readDelta(trackChunk, i);
		if(trackChunk.at(i)&0xf0) status=trackChunk.at(i++);
		Bytes event;
		event.push_back(status);
		switch(status&0xf0){
			case 0x80: case 0x90: case 0xa0: case 0xb0: case 0xe0:
				event+=slice(trackChunk, i, 2);
				i+=2;
				break;
			case 0xc0: case 0xd0:
				event.push_back(trackChunk.at(i++)); break;
			case 0xf0:
				if(status==0xff){
					int size=2+trackChunk.at(i+1);
					event+=slice(trackChunk, i, size);
					i+=size;
				}
				else event.push_back(trackChunk.at(i++));
				break;
			default: throw std::logic_error("impossible default");
		}
		pairs.push_back(Midi::Pair{delta, event});
	}
	if(pairs.back().event!=Bytes{0xff, 0x2f, 0}) throw std::runtime_error("invalid last command");
	return pairs;
}

static unsigned bigEndianToUnsigned(Bytes::const_iterator i, int size){
	unsigned result=0;
	for(int j=0; j<size; ++j){
		result<<=8;
		result+=*(i++);
	}
	return result;
}

//group the bytes of a MIDI file into header and tracks
static std::vector<Bytes> chunkitize(const Bytes& bytes){
	if(bytes.size()<HEADER_SIZE) throw std::runtime_error("header too short");
	if(slice(bytes, HEADER_TITLE.size())!=HEADER_TITLE) throw std::runtime_error("bad header");
	std::vector<Bytes> chunks;
	chunks.push_back(slice(bytes, HEADER_SIZE));
	unsigned i=HEADER_SIZE;
	while(bytes.size()>=i+TRACK_HEADER_SIZE){
		if(slice(bytes, i, TRACK_TITLE.size())!=TRACK_TITLE) throw std::runtime_error("bad track header");
		auto trackSize=TRACK_HEADER_SIZE+bigEndianToUnsigned(bytes.begin()+i+4, 4);
		if(bytes.size()<i+trackSize) throw std::runtime_error("track too long");
		chunks.push_back(slice(bytes, i, trackSize));
		i+=trackSize;
	}
	if(i!=bytes.size()) throw std::runtime_error("malformed tracks");
	if(bigEndianToUnsigned(bytes.begin()+10, 2)!=chunks.size()-1) throw std::runtime_error("bad size");
	return chunks;
}

Bytes toBigEndian(unsigned x, unsigned size){
	Bytes result;
	for(unsigned i=0; i<size; ++i) result.push_back((x>>((size-1-i)*8))&0xff);
	return result;
}

//Create MIDI track file bytes based on bytes.
//The track header and end message are appended automatically, so they should not be included.
static Bytes writeTrack(Bytes input){
	//some idiot midi players ignore the first delta time, so insert an empty text event if needed
	Bytes emptyTextEvent={0, 0xff, 0x01, 0};
	if(slice(input, emptyTextEvent.size())!=emptyTextEvent) input=emptyTextEvent+input;
	//
	input+=Bytes{1, 0xff, 0x2f, 0};
	return slice(TRACK_TITLE)+toBigEndian(input.size(), 4)+input;
}

/*-----Midi-----*/
Midi::Event::Event(int ticks, const std::vector<uint8_t>& data): ticks(ticks) {
	uint8_t type=data[0]&0xf0;
	this->type=SENTINEL;
	if(type==0x90&&data[2]){
		this->type=NOTE_ON;
		channel=data[0]&0x0f;
		note=data[1];
		velocityDown=data[2];
	}
	else if(type==0x80||type==0x90&&data[2]==0){
		this->type=NOTE_OFF;
		channel=data[0]&0x0f;
		note=data[1];
		velocityUp=data[2];
	}
	else if(data[0]==0xff){
		if(data[1]==0x51){
			this->type=TEMPO;
			usPerQuarter=bigEndianToUnsigned(data.begin()+3, 3);
		}
		else if(data[1]==0x58){
			this->type=TIME_SIG;
			timeSigTop=data[3];
			timeSigBottom=1<<data[4];
		}
		else if(data[1]==0x59){
			this->type=KEY_SIG;
			sharps=(int8_t)data[3];
			minor=data[4]!=0;
		}
	}
}

static uint8_t ilog2(int x){
	int result=-1;
	while(x){
		x>>=1;
		++result;
	}
	if(result==-1) throw std::logic_error("input outside domain");
	return result;
}

void Midi::Event::write(std::vector<uint8_t>& written) const {
	switch(type){
		case NOTE_ON: written+=bytes(
			0x90|channel, note, velocityDown
		); break;
		case NOTE_OFF: written+=bytes(
			0x80|channel, note, velocityUp
		); break;
		case TEMPO:
			written+=bytes(0xff, 0x51, 0x03)+toBigEndian(usPerQuarter, 3);
			break;
		case TIME_SIG: written+=bytes(
			0xff, 0x58, 0x04,
			timeSigTop, ilog2(timeSigBottom),
			24, 8
		); break;
		case KEY_SIG: written+=bytes(
			0xff, 0x59, 0x02,
			sharps<0?0x100+sharps:sharps, minor?1:0
		); break;
		default: throw std::logic_error("unhandled event");
	}
}

void Midi::append(unsigned track, int delta, const std::vector<uint8_t>& data){
	if(tracks.size()<=track) tracks.resize(track+1);
	int ticks=delta;
	if(tracks.at(track).size()) ticks+=tracks.at(track).back().ticks;
	tracks.at(track).push_back(Event(ticks, data));
}

void Midi::read(std::string fileName){
	Bytes bytes;
	std::ifstream file;
	file.open(fileName.c_str(), std::ios::binary);
	if(!file.is_open()) throw std::runtime_error("Couldn't open file or couldn't find file.");
	char c;
	while(file.get(c)) bytes.push_back((uint8_t)c);
	file.close();
	parse(bytes);
}

void Midi::write(std::string fileName) const {
	std::ofstream file;
	file.open(fileName.c_str(), std::ios::binary);
	if(!file.is_open()) throw std::runtime_error("couldn't open file");
	Bytes bytes;
	write(bytes);
	for(unsigned i=0; i<bytes.size(); ++i) file.put(bytes.at(i));
	file.close();
}

//parse bytes of a MIDI file, populate self
void Midi::parse(const Bytes& bytes){
	std::vector<Bytes> chunks=chunkitize(bytes);
	ticksPerQuarter=bigEndianToUnsigned(chunks.at(0).begin()+12, 2);
	if(ticksPerQuarter==0) throw std::runtime_error("invalid ticks per quarter");
	if(bigEndianToUnsigned(chunks.at(0).begin()+8, 2)!=1) throw std::runtime_error("unhandled file type");
	if(chunks.size()<2) return;
	for(unsigned i=1; i<chunks.size(); i++){//for all tracks
		int ticks=0;
		std::vector<Pair> pairs=getPairs(chunks.at(i));
		Track track;
		for(unsigned j=0; j<pairs.size(); j++){
			ticks+=pairs.at(j).delta;
			Event event(ticks, pairs.at(j).event);
			if(event.type!=Event::SENTINEL) track.push_back(event);
		}
		//conglomerate note on and off
		std::map<uint8_t, Event*> notes;
		for(auto j=track.begin(); j<track.end(); /*nothing*/){
			if(j->type==Event::NOTE_ON){
				if(notes.count(j->note)){
					track.erase(j);
					continue;
				}
				notes[j->note]=&*j;
			}
			if(j->type==Event::NOTE_OFF){
				if(notes.count(j->note)){
					auto& note=*notes.at(j->note);
					note.type=Event::NOTE;
					note.duration=j->ticks-note.ticks;
					note.velocityUp=j->velocityUp;
					notes.erase(j->note);
				}
				track.erase(j);
			}
			else ++j;
		}
		tracks.push_back(track);
	}
}

void Midi::write(Bytes& result) const {
	if(ticksPerQuarter==0) throw std::logic_error("invalid ticks per quarter");
	result+=HEADER_TITLE;
	result+=Bytes{0, 0, 0, 6, 0, 1};
	result+=toBigEndian(tracks.size(), 2);
	result+=toBigEndian(ticksPerQuarter, 2);
	for(unsigned i=0; i<tracks.size(); i++){
		std::vector<Event> split=tracks[i];
		splitNotes(split);
		//write
		int lastTicks=0;
		Bytes written;
		for(const auto& event: split){
			written+=writeDelta(event.ticks-lastTicks);
			event.write(written);
			lastTicks=event.ticks;
		}//for split events
		result+=writeTrack(written);
	}//for tracks
}

void splitNotes(Midi::Track& track){
	for(unsigned i=0; i<track.size(); ++i){
		if(track.at(i).type!=Midi::Event::NOTE) continue;
		track.at(i).type=Midi::Event::NOTE_ON;
		Midi::Event off=track.at(i);
		off.type=Midi::Event::NOTE_OFF;
		off.ticks+=off.duration;
		track.push_back(off);
	}
	std::sort(track.begin(), track.end());
}

std::vector<Midi::Pair> getPairs(Midi::Track track){
	splitNotes(track);
	std::vector<Midi::Pair> result;
	int last=0;
	for(const auto& i: track){
		Bytes written;
		i.write(written);
		result.push_back(Midi::Pair{i.ticks-last, written});
		last=i.ticks;
	}
	return result;
}

};//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Midi::Event& event){
	switch(event.type){
		case dlal::Midi::Event::TEMPO:
			o<<"tempo("   <<event.ticks<<"; "<<event.usPerQuarter<<")";
			break;
		case dlal::Midi::Event::TIME_SIG:
			o<<"time_sig("<<event.ticks<<"; "<<(int)event.timeSigTop<<", "<<(int)event.timeSigBottom<<")";
			break;
		case dlal::Midi::Event::KEY_SIG:
			o<<"key_sig(" <<event.ticks<<"; "<<event.sharps<<", "<<event.minor<<")";
			break;
		case dlal::Midi::Event::NOTE:
			o<<"note("    <<event.ticks<<"; "<<(int)event.note<<", "<<(int)event.velocityDown<<", "<<(int)event.duration<<", "<<(int)event.velocityUp<<")";
			break;
		case dlal::Midi::Event::NOTE_ON:
			o<<"note_on(" <<event.ticks<<"; "<<(int)event.note<<", "<<(int)event.velocityDown<<")";
			break;
		case dlal::Midi::Event::NOTE_OFF:
			o<<"note_off("<<event.ticks<<"; "<<(int)event.note<<", "<<(int)event.velocityUp<<")";
			break;
		case dlal::Midi::Event::SENTINEL:
			o<<"sentinel";
			break;
		default:
			o<<"bad";
			break;
	}
}

std::ostream& operator<<(std::ostream& o, const dlal::Midi::Pair& pair){
	return o<<"{"<<pair.delta<<", "<<pair.event<<"}";
}
