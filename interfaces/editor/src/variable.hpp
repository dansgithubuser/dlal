#ifndef VARIABLE_HPP_INCLUDED
#define VARIABLE_HPP_INCLUDED

#include "globals.hpp"
#include "object.hpp"

#include <wrapper.hpp>

#include <string>

#include <obvious.hpp>

struct Variable: public Object {
	Variable(){}
	Variable(std::string name, std::string value):
		_name(name), _value(value) {}

	void draw(bool selected) const {
		dans_sfml_wrapper_text_draw(mouseX(), mouseY(), SZ, text().c_str(), 0, 255, selected?255:0, 255);
	}

	bool contains(int mouseX, int mouseY) const {
		return
			this->mouseX()<mouseX&&mouseX<this->mouseX()+dans_sfml_wrapper_text_width(SZ, text().c_str())
			&&
			this->mouseY()<mouseY&&mouseY<this->mouseY()+SZ;
	}

	std::string text() const { return obvstr(_name, ": ", _value); }

	std::string _name, _value;
};

#endif
