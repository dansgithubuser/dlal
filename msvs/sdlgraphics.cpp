#include "sdlgraphics.hpp"

#include <sstream>

using namespace std;

void putpixel(int x, int y, int c, SDL_Surface* screenbuffer){
	if(x<screenbuffer->w&&y<screenbuffer->h&&x>=0&&y>=0){
		Uint32* pixels=(Uint32*)screenbuffer->pixels;
		pixels[screenbuffer->w*y+x]=c;
	}
	return;
}

void line(int x, int y, int dx, int dy, int c, SDL_Surface* screenbuffer){
	if(((x<0&&x+dx<0)||(x>screenbuffer->w&&x+dx>screenbuffer->w))&&
		((y<0&&y+dy<0)||(y>screenbuffer->h&&y+dy>screenbuffer->h))) return;
	if(abs(dx)>abs(dy)){
		if(dx>0){
			int max=x+dx;
			if(max>=screenbuffer->w) max=screenbuffer->w-1;
			if(x<0) x=0;
			for(int i=x; i<=max; i++)
				putpixel(i,(int)((float)(i-x)/dx*dy+y+0.5),c,screenbuffer);
		}
		else{
			int min=x+dx;
			if(min<0) min=0;
			if(x>=screenbuffer->w) x=screenbuffer->w-1;
			for(int i=x; i>=min; i--)
				putpixel(i,(int)((float)(i-x)/dx*dy+y+0.5),c,screenbuffer);
		}
	}
	else{
		if(dy>0){
			int max=y+dy;
			if(max>=screenbuffer->h) max=screenbuffer->h;
			if(y<0) y=0;
			for(int i=y; i<=max; i++)
				putpixel((int)((float)(i-y)/dy*dx+0.5)+x,i,c,screenbuffer);
		}
		else{
			int min=y+dy;
			if(min<0) min=0;
			if(y>=screenbuffer->h) y=screenbuffer->h-1;
			for(int i=y; i>=min; i--)
				putpixel((int)((float)(i-y)/dy*dx+0.5)+x,i,c,screenbuffer);
		}
	}
	return;
}

void box(int x, int y, int dx, int dy, int c, SDL_Surface* screenbuffer){
	line(x, y, dx, 0, c, screenbuffer);
	line(x, y, 0, dy, c, screenbuffer);
	line(x, y+dy, dx, 0, c, screenbuffer);
	line(x+dx, y, 0, dy, c, screenbuffer);
	return;
}

void cross(int x, int y, int dx, int dy, int c, SDL_Surface* screenbuffer){
	line(x, y, dx, dy, c, screenbuffer);
	line(x, y+dy, dx, -dy, c, screenbuffer);
}

void drawa(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void drawb(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size*3/4,0,c,screenbuffer);
	line(x+size*3/4,y,0,size/2,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y+size/2,0,size/2,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void drawc(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void drawd(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size/4,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size,size/4,0,c,screenbuffer);
	line(x+size/4,y,size/2,size/2,c,screenbuffer);
	line(x+size/4,y+size,size/2,-size/2,c,screenbuffer);
	return;
}

void drawe(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void drawf(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void drawg(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	line(x+size,y+size/2,0,size/2,c,screenbuffer);
	return;
}

void drawh(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	return;
}

void drawi(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/4,y,size/2,0,c,screenbuffer);
	line(x+size/4,y+size,size/2,0,c,screenbuffer);
	line(x+size/2,y,0,size,c,screenbuffer);
	return;
}

void drawj(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y,0,size,c,screenbuffer);
	line(x,y+size,size/2,0,c,screenbuffer);
	return;
}

void drawk(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,size/2,c,screenbuffer);
	line(x,y+size/2,size,-size/2,c,screenbuffer);
	return;
}

void drawl(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void drawm(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size/2,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	return;
}

void drawn(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	return;
}

void drawo(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void drawp(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x+size,y,0,size/2,c,screenbuffer);
	return;
}

void drawq(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size/2,c,screenbuffer);
	line(x,y+size,size/2,0,c,screenbuffer);
	line(x+size/2,y+size/2,size/2,size/2,c,screenbuffer);
	line(x+size,y+size/2,-size/2,size/2,c,screenbuffer);
	return;
}

void drawr(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x+size,y,0,size/2,c,screenbuffer);
	line(x,y+size/2,size,size/2,c,screenbuffer);
	return;
}

void draws(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size/2,c,screenbuffer);
	line(x+size,y+size/2,0,size/2,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void drawt(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x+size/2,y,0,size,c,screenbuffer);
	return;
}

void drawu(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void drawv(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size/2,size,c,screenbuffer);
	line(x+size,y,-size/2,size,c,screenbuffer);
	return;
}

void draww(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y+size,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size/2,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	return;
}

void drawx(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,size,c,screenbuffer);
	line(x+size,y,-size,size,c,screenbuffer);
	return;
}

void drawy(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size/2,size/2,c,screenbuffer);
	line(x+size,y,-size/2,size/2,c,screenbuffer);
	line(x+size/2,y+size/2,0,size/2,c,screenbuffer);
	return;
}

void drawz(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	line(x+size,y,-size,size,c,screenbuffer);
	return;
}

void drawcolon(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	putpixel(x+size/2, y+size*3/4, c, screenbuffer);
	putpixel(x+size/2, y+size/4, c, screenbuffer);
}

void drawhack(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,size,c,screenbuffer);
	return;
}

void drawslash(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size,y,-size,size,c,screenbuffer);
	return;
}

void draw1(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y,0,size,c,screenbuffer);
	line(x+size/2,y,-size/4,size/4,c,screenbuffer);
	return;
}

void draw2(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x+size,y,0,size/2,c,screenbuffer);
	line(x,y+size/2,0,size/2,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void draw3(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void draw4(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x,y,0,size/2,c,screenbuffer);
	return;
}

void draw5(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size/2,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x+size,y+size/2,0,size/2,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void draw6(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x+size,y+size/2,0,size/2,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void draw7(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	return;
}

void draw8(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void draw9(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size/2,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void draw0(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y,size,0,c,screenbuffer);
	line(x,y,0,size,c,screenbuffer);
	line(x+size,y,0,size,c,screenbuffer);
	line(x,y+size,size,0,c,screenbuffer);
	putpixel(x+size/2, y+size/2, c, screenbuffer);
	return;
}

void draw_(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y+size,size,0,c,screenbuffer);
	return;
}

void drawcomma(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y+size-1,-size/4,size/4,c,screenbuffer);
	return;
}

void drawdot(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	putpixel(x+size/2, y+size, c, screenbuffer);
	return;
}

void drawapostrophe(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y,-size/4,size/4,c,screenbuffer);
	return;
}

void drawdash(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void drawbang(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y,0,size*3/4,c,screenbuffer);
	line(x+size/2,y+size,1,1,c,screenbuffer);
	return;
}

void drawinterro(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y+size/2,0,size/4,c,screenbuffer);
	line(x+size/2,y+size/2,size/2,0,c,screenbuffer);
	line(x+size,y,0,size/2,c,screenbuffer);
	line(x,y,size,0,c,screenbuffer);
	line(x+size/2,y+size,1,1,c,screenbuffer);
	return;
}

void drawtick(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y,size/4,size/4,c,screenbuffer);
	return;
}

void drawocto(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/4,y,0,size,c,screenbuffer);
	line(x+size*3/4,y,0,size,c,screenbuffer);
	line(x,y+size/4,size,0,c,screenbuffer);
	line(x,y+size*3/4,size,0,c,screenbuffer);
	return;
}

void drawplus(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/2,y,0,size,c,screenbuffer);
	line(x,y+size/2,size,0,c,screenbuffer);
	return;
}

void drawtilde(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x, y+size*2/3, size/3, -size/3, c, screenbuffer);
	line(x+size/3, y+size/3, size/3, size/3, c, screenbuffer);
	line(x+size*2/3, y+size*2/3, size/3, -size/3, c, screenbuffer);
}

void drawsemicolon(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	drawcomma(x, y, c, screenbuffer, size);
	putpixel(x+size/2, y+size/4, c, screenbuffer);
}

void drawopenparen(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+3*size/4, y+size/4, size/4, -size/4, c, screenbuffer);
	line(x+3*size/4, y+size/4, 0, size/2, c, screenbuffer);
	line(x+3*size/4, y+3*size/4, size/4, size/4, c, screenbuffer);
}

void drawcloseparen(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x, y, size/4, size/4, c, screenbuffer);
	line(x+size/4, y+size/4, 0, size/2, c, screenbuffer);
	line(x+size/4, y+3*size/4, -size/4, size/4, c, screenbuffer);
}

void drawasterisk(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/4, y+size/4, size/2, 0, c, screenbuffer);
	line(x+size/3, y, size/3, size/2, c, screenbuffer);
	line(x+size/3, y+size/2, size/3, -size/2, c, screenbuffer);
}

void drawampersand(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x+size/8, y+size/4, 3*size/4, 3*size/4, c, screenbuffer);
	line(x+size/8, y+size/4, size/4, -size/4, c, screenbuffer);
	line(x+3*size/8, y, size/4, size/4, c, screenbuffer);
	line(x+size/8, y+3*size/4, size/2, -size/2, c, screenbuffer);
	line(x+size/8, y+3*size/4, size/4, size/4, c, screenbuffer);
	line(x+3*size/8, y+size, size/2, -size/2, c, screenbuffer);
}

void drawunderscore(int x, int y, int c, SDL_Surface* screenbuffer, int size){
	line(x, y+size, size, 0, c, screenbuffer);
}

void outtext(int x, int y, int c, string s, SDL_Surface* screenbuffer, int size){
	int o=0;
	for(int i=0; i<(int)s.length(); i++){
		switch(s[i]){
			case 'a': case 'A': drawa(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'b': case 'B': drawb(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'c': case 'C': drawc(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'd': case 'D': drawd(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'e': case 'E': drawe(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'f': case 'F': drawf(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'g': case 'G': drawg(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'h': case 'H': drawh(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'i': case 'I': drawi(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'j': case 'J': drawj(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'k': case 'K': drawk(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'l': case 'L': drawl(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'm': case 'M': drawm(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'n': case 'N': drawn(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'o': case 'O': drawo(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'p': case 'P': drawp(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'q': case 'Q': drawq(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'r': case 'R': drawr(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 's': case 'S': draws(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 't': case 'T': drawt(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'u': case 'U': drawu(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'v': case 'V': drawv(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'w': case 'W': draww(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'x': case 'X': drawx(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'y': case 'Y': drawy(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case 'z': case 'Z': drawz(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '1': draw1(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '2': draw2(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '3': draw3(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '4': draw4(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '5': draw5(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '6': draw6(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '7': draw7(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '8': draw8(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '9': draw9(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '0': draw0(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '\'': drawapostrophe(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '/': drawslash(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case ',': drawcomma(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '.': drawdot(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '-': drawdash(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '!': drawbang(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '?': drawinterro(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '`': drawtick(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '#': drawocto(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '+': drawplus(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case ':': drawcolon(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '~': drawtilde(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case ';': drawsemicolon(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '(': drawopenparen(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case ')': drawcloseparen(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '*': drawasterisk(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '&': drawampersand(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '_': drawunderscore(x+(size*5/4+1)*o,y,c,screenbuffer,size); break;
			case '\n': y+=size*5/2+2; --o; break;
			case '\r': o=-1; break;
			default: break;
		}
		++o;
	}
	return;
}

void outdouble(int x, int y, int c, double d, SDL_Surface* screenbuffer, int size){
	stringstream ss;
	ss<<d;
	string s=ss.str();
	outtext(x,y,c,s,screenbuffer,size);
	return;
}

void outint(int x, int y, int c, int z, SDL_Surface* screenbuffer, int size){
	stringstream ss;
	ss<<z;
	string s=ss.str();
	outtext(x,y,c,s,screenbuffer,size);
	return;
}

void outchar(int x, int y, int c, char k, SDL_Surface* screenbuffer, int size){
	switch(k){
		case 'a': case 'A': drawa(x,y,c,screenbuffer,size); break;
		case 'b': case 'B': drawb(x,y,c,screenbuffer,size); break;
		case 'c': case 'C': drawc(x,y,c,screenbuffer,size); break;
		case 'd': case 'D': drawd(x,y,c,screenbuffer,size); break;
		case 'e': case 'E': drawe(x,y,c,screenbuffer,size); break;
		case 'f': case 'F': drawf(x,y,c,screenbuffer,size); break;
		case 'g': case 'G': drawg(x,y,c,screenbuffer,size); break;
		case 'h': case 'H': drawh(x,y,c,screenbuffer,size); break;
		case 'i': case 'I': drawi(x,y,c,screenbuffer,size); break;
		case 'j': case 'J': drawj(x,y,c,screenbuffer,size); break;
		case 'k': case 'K': drawk(x,y,c,screenbuffer,size); break;
		case 'l': case 'L': drawl(x,y,c,screenbuffer,size); break;
		case 'm': case 'M': drawm(x,y,c,screenbuffer,size); break;
		case 'n': case 'N': drawn(x,y,c,screenbuffer,size); break;
		case 'o': case 'O': drawo(x,y,c,screenbuffer,size); break;
		case 'p': case 'P': drawp(x,y,c,screenbuffer,size); break;
		case 'q': case 'Q': drawq(x,y,c,screenbuffer,size); break;
		case 'r': case 'R': drawr(x,y,c,screenbuffer,size); break;
		case 's': case 'S': draws(x,y,c,screenbuffer,size); break;
		case 't': case 'T': drawt(x,y,c,screenbuffer,size); break;
		case 'u': case 'U': drawu(x,y,c,screenbuffer,size); break;
		case 'v': case 'V': drawv(x,y,c,screenbuffer,size); break;
		case 'w': case 'W': draww(x,y,c,screenbuffer,size); break;
		case 'x': case 'X': drawx(x,y,c,screenbuffer,size); break;
		case 'y': case 'Y': drawy(x,y,c,screenbuffer,size); break;
		case 'z': case 'Z': drawz(x,y,c,screenbuffer,size); break;
		case '1': draw1(x,y,c,screenbuffer,size); break;
		case '2': draw2(x,y,c,screenbuffer,size); break;
		case '3': draw3(x,y,c,screenbuffer,size); break;
		case '4': draw4(x,y,c,screenbuffer,size); break;
		case '5': draw5(x,y,c,screenbuffer,size); break;
		case '6': draw6(x,y,c,screenbuffer,size); break;
		case '7': draw7(x,y,c,screenbuffer,size); break;
		case '8': draw8(x,y,c,screenbuffer,size); break;
		case '9': draw9(x,y,c,screenbuffer,size); break;
		case '0': draw0(x,y,c,screenbuffer,size); break;
		case '\'': drawapostrophe(x,y,c,screenbuffer,size); break;
		case '/': drawslash(x,y,c,screenbuffer,size); break;
		case ',': drawcomma(x,y,c,screenbuffer,size); break;
		case '.': drawdot(x,y,c,screenbuffer,size); break;
		case '-': drawdash(x,y,c,screenbuffer,size); break;
		case '!': drawbang(x,y,c,screenbuffer,size); break;
		case '?': drawinterro(x,y,c,screenbuffer,size); break;
		case '`': drawtick(x,y,c,screenbuffer,size); break;
		case '#': drawocto(x,y,c,screenbuffer,size); break;
		case '+': drawplus(x,y,c,screenbuffer,size); break;
		case ':': drawcolon(x,y,c,screenbuffer,size); break;
		case '~': drawtilde(x,y,c,screenbuffer,size); break;
		case ';': drawsemicolon(x,y,c,screenbuffer,size); break;
		case '(': drawopenparen(x,y,c,screenbuffer,size); break;
		case ')': drawcloseparen(x,y,c,screenbuffer,size); break;
		case '*': drawasterisk(x,y,c,screenbuffer,size); break;
		case '&': drawampersand(x,y,c,screenbuffer,size); break;
		case '_': drawunderscore(x,y,c,screenbuffer,size); break;
		default: break;
	}
	return;
}
