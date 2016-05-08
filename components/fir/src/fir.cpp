#include "fir.hpp"

#include <cmath>
#include <fstream>
#include <iostream>

#define __SIMPLE_FFT__FFT_SETTINGS_H__
typedef double real_type;
typedef std::complex<real_type> complex_type;
#define __USE_SQUARE_BRACKETS_FOR_ELEMENT_ACCESS_OPERATOR
#include <simple_fft/fft.h>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Fir; }

namespace dlal{

static void real(std::vector<real_type>& result, const std::vector<complex_type>& x){
	for(unsigned i=0; i<x.size(); ++i) result[i]=x[i].real();
}

static std::vector<real_type> getSequence(std::stringstream& ss){
	real_type s;
	std::vector<real_type> x;
	while(ss>>s) x.push_back(s);
	return x;
}

static void frToIr(const std::vector<real_type>& fr, std::vector<real_type>& ir){
	const char* error=nullptr;
	static std::vector<complex_type> cfr(fr.size()*2);
	static std::vector<complex_type> cir(fr.size()*2);
	for(unsigned i=0; i<fr.size(); ++i){
		cfr[             i]=fr[i];
		cfr[cfr.size()-1-i]=fr[i];
	}
	if(!simple_fft::IFFT(cfr, cir, fr.size(), error)) std::cerr<<error;
	for(unsigned i=0; i<fr.size(); ++i) ir[i]=cir[i].real();
}

Fir::Fir(){
	_checkAudio=true;
	registerCommand("fft", "<sample[0]..sample[n]>", [this](std::stringstream& ss){
		auto x=getSequence(ss);
		std::vector<complex_type> y(x.size());
		const char* error=nullptr;
		if(!simple_fft::FFT(x, y, x.size(), error)) return "error: "+std::string(error);
		std::stringstream tt;
		for(auto i: y) tt<<i.real()<<" "<<i.imag()<<"\n";
		return tt.str();
	});
	registerCommand("fr", "<magnitude[0]..magnitude[n]>", [this](std::stringstream& ss)->std::string{
		auto x=getSequence(ss);
		if(_samplesPerEvaluation&&x.size()!=_ir.size()) return "error: cannot resize after adding";
		resize(x.size());
		frToIr(x, _ir);
		return "";
	});
	registerCommand("resize", "<impulse response size in samples>", [this](std::stringstream& ss){
		if(_samplesPerEvaluation) return "error: cannot resize after adding";
		unsigned size;
		ss>>size;
		resize(size);
		return "";
	});
	registerCommand("formant", "i frequency magnitude <width (Hz)> speed", [this](std::stringstream& ss){
		unsigned i;
		float frequency, magnitude, width, speed;
		ss>>i>>frequency>>magnitude>>width>>speed;
		Formant f(frequency, magnitude, width, speed);
		if(i>=_formants.size()){
			_formants.resize(i+1);
			_formants[i]=std::make_pair(f, f);
		}
		else{
			if(speed==1.0f) _formants[i].first=f;
			_formants[i].second=f;
		}
		return "";
	});
	registerCommand("formant_mute", "i speed", [this](std::stringstream& ss){
		unsigned i;
		float speed;
		ss>>i>>speed;
		if(i<_formants.size()){
			Formant f(_formants[i].first._frequency, 0.0f, _formants[i].first._width, speed);
			if(speed==1.0f) _formants[i].first=f;
			_formants[i].second=f;
		}
		return "";
	});
	registerCommand("save_formant_fr", "<file name>", [this](std::stringstream& ss){
		std::vector<real_type> fr;
		fr.resize(_ir.size());
		for(auto& i: _formants) i.first.apply(fr, _sampleRate);
		std::string fileName;
		ss>>fileName;
		std::ofstream file(fileName.c_str());
		for(unsigned i=0; i<fr.size(); ++i) file<<fr[i]<<"\n";
		return "";
	});
}

std::string Fir::connect(Component& output){
	auto s=MultiOut::connect(output);
	if(dlal::isError(s)) return s;
	_x.push_back(std::make_pair(
		&output,
		Ringbuffer<float>(_ir.size(), 0.0f)
	));
	return "";
}

std::string Fir::disconnect(Component& output){
	auto s=MultiOut::disconnect(output);
	if(dlal::isError(s)) return s;
	for(unsigned i=0; i<_x.size(); ++i)
		if(_x[i].first==&output){ _x.erase(_x.begin()+i); break; }
	return "";
}

void Fir::evaluate(){
	//get frequency response from formants, if any
	{
		static std::vector<real_type> fr(_ir.size());
		std::fill(fr.begin(), fr.end(), real_type(0));
		for(auto& i: _formants){
			i.first.toward(i.second);
			i.first.apply(fr, _sampleRate);
		}
		if(!_formants.empty()) frToIr(fr, _ir);
	}
	//filter
	for(unsigned i=0; i<_outputs.size(); ++i){
		for(unsigned j=0; j<_samplesPerEvaluation; ++j){
			_x[i].second.write(_outputs[i]->audio()[j]);
			const auto& x=_x[i].second;
			real_type y(0);
			for(unsigned k=0; k<_ir.size(); ++k) y+=_ir[k]*x.read(k);
			_outputs[i]->audio()[j]=(float)y;
		}
	}
}

Fir::Formant::Formant(): _frequency(0.0f), _magnitude(0.0f), _width(0.0f), _speed(0.0f) {}

Fir::Formant::Formant(float frequency, float magnitude, float width, float speed):
	_frequency(frequency), _magnitude(magnitude), _width(width), _speed(speed)
{}

void Fir::Formant::toward(const Formant& d){
	auto toward=[](float& s, float d, float speed){ s=speed*d+(1-speed)*s; };
	toward(_frequency, d._frequency, d._speed);
	toward(_magnitude, d._magnitude, d._speed);
	toward(_width    , d._width    , d._speed);
}

void Fir::Formant::apply(std::vector<real_type>& fr, unsigned sampleRate){
	if(_width==0) return;
	for(unsigned i=0; i<fr.size(); ++i){
		float x=_frequency-sampleRate/2*i/fr.size();
		fr[i]+=_magnitude*std::exp(-x*x/_width);
	}
}

void Fir::resize(unsigned size){
	_ir.resize(size, real_type(0));
	for(auto& i: _x) i.second=Ringbuffer<float>(size, 0.0f);
}

}//namespace dlal
