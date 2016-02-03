#include "lpf.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Lpf; }

namespace dlal{

Lpf::Lpf(): _lowness(0.5f), _control(-1), _listening(false) {
	_checkAudio=true;
	_f.push_back(0.0f);
	_f.push_back(1.0f);
	registerCommand("set", "lowness", [this](std::stringstream& ss){
		ss>>_lowness;
		return "";
	});
	registerCommand("listen", "y/n", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		_listening=s=="y";
		if(_listening){
			_listeningControls.clear();
			return "listening";
		}
		if(_listeningControls.size()){
			auto a=_listeningControls.begin();
			_control=a->first;
			_min=a->second._min;
			_max=a->second._max;
			int maxRange=a->second;
			if(_control==PITCH_WHEEL_PRETEND_CONTROL) maxRange>>=7;
			for(auto i: _listeningControls) if(i.second>maxRange){
				if(i.first==PITCH_WHEEL_PRETEND_CONTROL&&i.second>>7<=maxRange) continue;
				_control=i.first;
				_min=i.second._min;
				_max=i.second._max;
				maxRange=i.second;
			}
			return ("control "+std::to_string(_control)+" range "+std::to_string(_min)+".."+std::to_string(_max)).c_str();
		}
		return "";
	});
	registerCommand("function", "y[1]..y[n]", [this](std::stringstream& ss){
		_f.clear();
		float f;
		while(ss>>f) _f.push_back(f);
		if(_f.empty()){
			_f.push_back(0.0f);
			_f.push_back(1.0f);
		}
		return "";
	});
}

void Lpf::evaluate(){
	for(auto output: _outputs){
		float& y1=_y[output]._;
		for(unsigned i=0; i<_samplesPerEvaluation; ++i){
			float& y2=output->audio()[i];
			y2=(1-_lowness)*y2+_lowness*y1;
			y1=y2;
		}
	}
}

void Lpf::midi(const uint8_t* bytes, unsigned size){
	if(size!=3) return;
	bool good=false;
	int value, controller;
	switch(bytes[0]&0xf0){
		case 0xb0:
			good=bytes[1]==_control;
			value=bytes[2];
			controller=bytes[1];
			break;
		case 0xe0:
			good=PITCH_WHEEL_PRETEND_CONTROL==_control;
			value=(bytes[2]<<7)+bytes[1];
			controller=PITCH_WHEEL_PRETEND_CONTROL;
			break;
		default: break;
	}
	if(_listening) _listeningControls[controller].value(value);
	if(good){
		float f=1.0f*(value-_min)/(_max-_min)*(_f.size()-1);
		int i=int(f);
		float j=f-i;
		if(i>=(int)_f.size()-1) _lowness=_f.back();
		else if(i<0) _lowness=_f.front();
		else _lowness=(1-j)*_f[i]+j*_f[i+1];
	}
}

}//namespace dlal
