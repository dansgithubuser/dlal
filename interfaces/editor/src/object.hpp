#ifndef OBJECT_HPP_INCLUDED
#define OBJECT_HPP_INCLUDED

#include "globals.hpp"

struct Object{
	void moveTo(int x, int y){
		_xRaw=x;
		_yRaw=y;
		_x=x/SZ*SZ;
		_y=y/SZ*SZ;
	}
	void moveBy(int x, int y){
		moveTo(_xRaw+x, _yRaw+y);
	}
	virtual bool contains(int mouseX, int mouseY) const =0;
	int mouseX() const { return _x+(_dx?*_dx:0); }
	int mouseY() const { return _y+(_dy?*_dy:0); }
	int _x, _y, _xRaw, _yRaw;
	int* _dx=nullptr;
	int* _dy=nullptr;
};

#endif
