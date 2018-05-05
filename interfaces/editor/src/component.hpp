#ifndef COMPONENT_HPP_INCLUDED
#define COMPONENT_HPP_INCLUDED

#include "object.hpp"
#include "connection.hpp"

#include <wrapper.hpp>

#include <map>
#include <string>

struct Component: public Object {
	Component& name(std::string s){ _name=s; return *this; }

	Component& set(std::string name, std::string type, int x, int y, int* dx=nullptr, int* dy=nullptr){
		_name=name;
		_type=type;
		moveTo(x, y);
		_dx=dx; _dy=dy;
		return *this;
	}

	void dialpad(std::string pattern, sf::VertexArray& va, bool selected, bool bright=false) const {
		auto color=sf::Color(0, bright?255:64, selected?255:0);
		for(size_t i=0; i<pattern.size()-1; ++i){
			if(pattern[i+1]=='-'){ ++i; continue; }
			int xi=(std::stoi(pattern.substr(i+0, 1))-1)%3;
			int yi=(std::stoi(pattern.substr(i+0, 1))-1)/3;
			int xf=(std::stoi(pattern.substr(i+1, 1))-1)%3;
			int yf=(std::stoi(pattern.substr(i+1, 1))-1)/3;
			va.append(sf::Vertex(sf::Vector2f(mouseX()+SZ*xi, mouseY()+SZ*yi), color));
			va.append(sf::Vertex(sf::Vector2f(mouseX()+SZ*xf, mouseY()+SZ*yf), color));
		}
	}


	void draw(sf::VertexArray& va, bool selected, bool type=false){
		if(!_type.size()) return;
		dans_sfml_wrapper_text_draw(
			mouseX()+2*SZ+2, mouseY(),
			SZ, _label.c_str(), 0, 128, 0, 255
		);
		if(type) _message=_type;
		dans_sfml_wrapper_text_draw(
			mouseX()+2*SZ+2, mouseY()+SZ,
			SZ, _message.c_str(), 0, 128, 0, 255
		);
		dialpad("79317", va, selected);
		std::map<std::string, std::string> sketches={
			{"arpeggiator", "72-83"},
			{"audio", "24862"},
			{"buffer", "4286"},
			{"commander", "3179"},
			{"converter", "971381"},
			{"filea", "317-46"},
			{"filei", "317-458"},
			{"fileo", "317-452"},
			{"fir", "7297"},
			{"liner", "46"},
			{"lpf", "71289"},
			{"midi", "427-829-26"},
			{"midichlorian", "14863-28"},
			{"multiplier", "73-19"},
			{"network", "715893"},
			{"peak", "729"},
			{"raw", "713649"},
			{"reticulated_liner", "46-17-28-39"},
			{"sonic", "3197"},
			{"soundfont", "3187-28-56"},
			{"vst", "183"},
		};
		if(sketches.count(_type)) dialpad(sketches.at(_type), va, selected, true);
		if(_phase){
			int xPhase=mouseX()+2*SZ*_phase;
			va.append(sf::Vertex(sf::Vector2f(xPhase, mouseY()     ), sf::Color(0, 0, 255)));
			va.append(sf::Vertex(sf::Vector2f(xPhase, mouseY()+2*SZ), sf::Color(0, 0, 255)));
		}
		for(auto& i: _connections) i.second.draw(va);
	}

	bool contains(int mouseX, int mouseY) const {
		return
			this->mouseX()<mouseX&&mouseX<this->mouseX()+2*SZ
			&&
			this->mouseY()<mouseY&&mouseY<this->mouseY()+2*SZ;
	}

	void name(){
		_message=_name;
	}

	std::string _name;
	std::string _type;
	std::map<std::string, Connection> _connections;
	float _phase=0.0f;
	std::string _label;
	std::string _message;
};

#endif
