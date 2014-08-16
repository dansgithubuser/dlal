#ifndef _SDLGRAPHICS_H
#define _SDLGRAPHICS_H

#include "SDL/SDL.h"

#include <string>

void putpixel(int x, int y, int c, SDL_Surface* screenbuffer);
void line(int x, int y, int dx, int dy, int c, SDL_Surface* screenbuffer);
void box(int x, int y, int dx, int dy, int c, SDL_Surface* screenbuffer);
void cross(int x, int y, int dx, int dy, int c, SDL_Surface* screenbuffer);

void drawa(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawb(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawc(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawd(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawe(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawf(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawg(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawh(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawi(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawj(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawk(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawl(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawm(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawn(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawo(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawp(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawq(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawr(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draws(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawt(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawu(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawv(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draww(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawx(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawy(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawz(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawcolon(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawslash(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw1(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);	
void draw2(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw3(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw4(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw5(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw6(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw7(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw8(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw9(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw0(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void draw_(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawcomma(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawdot(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawapostrophe(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawdash(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawbang(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawinterro(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawtick(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawocto(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawplus(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawtilde(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawsemicolon(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawopenparen(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawcloseparen(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawasterisk(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawampersand(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);
void drawunderscore(int x, int y, int c, SDL_Surface* screenbuffer, int size=8);

void outtext(int x, int y, int c, std::string s, SDL_Surface* screenbuffer, int size=8);
void outdouble(int x, int y, int c, double d, SDL_Surface* screenbuffer, int size=8);
void outint(int x, int y, int c, int z, SDL_Surface* screenbuffer, int size=8);
void outchar(int x, int y, int c, char k, SDL_Surface* screenbuffer, int size=8);

template <typename any>
void plot(
	int x,
	int y,
	int c,
	any* f,
	int start,
	int stopbefore,
	double scalex,
	double scaley,
	SDL_Surface* screenbuffer)
{
	for(int i=start; i<stopbefore; i++)
		putpixel((int)(x+i*scalex),y+(int)(f[i]*scaley),c,screenbuffer);
}

#endif
