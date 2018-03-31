#include <dryad.hpp>
#include <wrapper.hpp>

#include <map>
#include <string>

#include <obvious.hpp>

static const int SZ=8;

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
	virtual bool contains(int x, int y) const =0;
	int _x, _y, _xRaw, _yRaw;
};

struct Connection;
struct Component;

struct Connection{
	Connection(){}
	Connection(Component* src, Component* dst): _src(src), _dst(dst) {}

	void draw(sf::VertexArray& va);

	Component* _src;
	Component* _dst;
	float _commandHeat=0.0f, _midiHeat=0.0f;
};

struct Component: public Object {
	Component(){}

	void set(std::string type, int x, int y){
		_type=type;
		moveTo(x, y);
	}

	void dialpad(std::string pattern, sf::VertexArray& va) const;

	void draw(sf::VertexArray& va){
		dans_sfml_wrapper_text_draw(_x+2*SZ+2, _y, SZ, _label.c_str(), 0, 128, 0, 255);
		dialpad("79317", va);
		std::map<std::string, std::string> sketches={
			{"audio", "24862"},
			{"buffer", "4286"},
			{"commander", "1937"},
			{"liner", "46"},
			{"midi", "183"},
			{"network", "19"},
		};
		if(sketches.count(_type)) dialpad(sketches.at(_type), va);
		if(_phase){
			int x=_x+2*SZ*_phase;
			va.append(sf::Vertex(sf::Vector2f(x, _y     ), sf::Color(0, 0, 255)));
			va.append(sf::Vertex(sf::Vector2f(x, _y+2*SZ), sf::Color(0, 0, 255)));
		}
		for(auto& i: _connections) i.second.draw(va);
	}

	bool contains(int x, int y) const { return _x<x&&x<_x+2*SZ&&_y<y&&y<_y+2*SZ; }

	std::string _type;
	std::map<std::string, Connection> _connections;
	float _phase=0.0f;
	std::string _label;
};

void Connection::draw(sf::VertexArray& va){
	int    midiHeat=int(512*   _midiHeat);
	int commandHeat=int(512*_commandHeat);
	_midiHeat   /=2;
	_commandHeat/=2;
	const sf::Color cn(std::min(255, midiHeat   ), std::min(255, commandHeat+64),  0, 128);
	const sf::Color cf(std::min(255, midiHeat+64), std::min(255, commandHeat+64),  0, 128);
	const sf::Color cb(std::min(255, midiHeat   ), std::min(255, commandHeat+64), 64, 128);
	std::vector<sf::Vertex> v;
	v.push_back(sf::Vertex(sf::Vector2f(_src->_x+SZ, _src->_y+2*SZ), cn));//source
	if(_dst->_y>_src->_y){//destination below
		if(_dst->_y-_src->_y<=5*SZ){//directly below
			v.push_back(sf::Vertex(sf::Vector2f(_src->_x+SZ, _dst->_y-SZ), cn));//drop to just above destination
		}
		else{
			v.push_back(sf::Vertex(sf::Vector2f(_src->_x   , _src->_y+3*SZ), cf));//diagonal
			v.push_back(sf::Vertex(sf::Vector2f(_src->_x-SZ, _src->_y+4*SZ), cf));//diagonal
			v.push_back(sf::Vertex(sf::Vector2f(_src->_x-SZ, _dst->_y-2*SZ), cf));//drop to just above destination
			v.push_back(sf::Vertex(sf::Vector2f(_src->_x   , _dst->_y-  SZ), cn));//diagonal
		}
	}
	else{
		v.push_back(sf::Vertex(sf::Vector2f(_src->_x+2*SZ, _src->_y+3*SZ), cn));//diagonal
		v.push_back(sf::Vertex(sf::Vector2f(_src->_x+3*SZ, _src->_y+2*SZ), cb));//diagonal
		v.push_back(sf::Vertex(sf::Vector2f(_src->_x+3*SZ, _dst->_y     ), cb));//align vertically
		v.push_back(sf::Vertex(sf::Vector2f(_src->_x+2*SZ, _dst->_y-  SZ), cn));//diagonal
	}
	v.push_back(sf::Vertex(sf::Vector2f(_dst->_x+SZ, _dst->_y-SZ), cn));//align horizontally
	v.push_back(sf::Vertex(sf::Vector2f(_dst->_x+SZ, _dst->_y   ), cn));//destination
	for(size_t i=0; i<v.size()-1; ++i){
		va.append(v[i+0]);
		va.append(v[i+1]);
	}
}

struct Variable: public Object {
	Variable(){}
	Variable(std::string name, std::string value):
		_name(name), _value(value) {}

	void draw() const;

	bool contains(int x, int y) const {
		return _x<x&&x<_x+dans_sfml_wrapper_text_width(SZ, text().c_str())&&_y<y&&y<_y+SZ;
	}

	std::string text() const { return obvstr(_name, ": ", _value); }

	std::string _name, _value;
};

struct Button{
	bool pressed=false;
	int x, y;
	int xTo(int newX){
		int dx=newX-x;
		x=newX;
		return dx;
	}
	int yTo(int newY){
		int dy=newY-y;
		y=newY;
		return dy;
	}
	void press(int newX, int newY){
		x=newX;
		y=newY;
		pressed=true;
	}
};

dryad::Client* fClient=nullptr;
std::string fString;
std::string fText;
std::map<std::string, Variable> fVariables;
std::map<std::string, Component> fComponents;
Button fButtons[2];
std::vector<Object*> fSelected;

void Component::dialpad(std::string pattern, sf::VertexArray& va) const {
	auto color=sf::Color(0, in(this, fSelected)?255:128, 0);
	for(size_t i=0; i<pattern.size()-1; ++i){
		int xi=(std::stoi(obvstr(pattern[i+0]))-1)%3;
		int yi=(std::stoi(obvstr(pattern[i+0]))-1)/3;
		int xf=(std::stoi(obvstr(pattern[i+1]))-1)%3;
		int yf=(std::stoi(obvstr(pattern[i+1]))-1)/3;
		va.append(sf::Vertex(sf::Vector2f(_x+SZ*xi, _y+SZ*yi), color));
		va.append(sf::Vertex(sf::Vector2f(_x+SZ*xf, _y+SZ*yf), color));
	}
}

void Variable::draw() const {
	dans_sfml_wrapper_text_draw(_x, _y, SZ, text().c_str(), 0, in(this, fSelected)?255:128, 0, 255);
}

extern "C" {
	void editor_init(const char* host, int port){
		fClient=new dryad::Client(host, port);
	}

	void editor_finish(){
		delete fClient;
	}

	const char* editor_dryad_read(){
		if(!fClient) return nullptr;
		return fClient->readSizedString(fString)?fString.c_str():"";
	}

	int editor_dryad_times_disconnected(){
		if(!fClient) return -1;
		return fClient->timesDisconnected();
	}

	void editor_set_text(const char* s){
		fText=s;
	}

	void editor_button(int button, int pressed, int x, int y){
		if(button==0){
			if(pressed){
				fButtons[0].press(x, y);
				std::vector<Object*> objects;
				for(auto& i: fComponents) objects.push_back(&i.second);
				for(auto& i: fVariables) objects.push_back(&i.second);
				for(auto i: objects) if(i->contains(x, y)&&!in(i, fSelected)){
					fSelected.push_back(i);
					break;
				}
			}
			else fButtons[0].pressed=false;
		}
	}

	void editor_move(int x, int y){
		if(fButtons[0].pressed){
			int dx=fButtons[0].xTo(x);
			int dy=fButtons[0].yTo(y);
			for(auto i: fSelected) i->moveBy(dx, dy);
		}
	}

	void editor_deselect(){ fSelected.clear(); }

	void editor_draw(){
		gDansSfmlWrapperBoss->window.clear();
		static sf::VertexArray va(sf::PrimitiveType::Lines);
		for(auto& i: fComponents) i.second.draw(va);
		gDansSfmlWrapperBoss->window.draw(va, sf::RenderStates(sf::BlendMode(
			sf::BlendMode::Factor::One, sf::BlendMode::Factor::OneMinusSrcAlpha
		)));
		va.clear();
		for(const auto& i: fVariables) i.second.draw();
		dans_sfml_wrapper_text_draw(SZ, gDansSfmlWrapperBoss->window.getSize().y-SZ, SZ, fText.c_str(), 255, 255, 255, 255);
		gDansSfmlWrapperBoss->window.display();
	}

	void variable_set(const char* name, const char* value){
		if(fVariables.count(name)) fVariables.at(name)._value=value;
		else{
			Variable v(name, value);
			v.moveTo(400, SZ*fVariables.size());
			fVariables[name]=v;
		}
	}

	void component_new(const char* name, const char* type, int x, int y){
		fComponents[name].set(type, x, y);
	}

	void component_label(const char* name, const char* label){
		fComponents[name]._label=label;
	}

	void component_phase(const char* name, float phase){
		if(!fComponents.count(name)) return;
		fComponents.at(name)._phase=phase;
	}

	void connection_new(const char* src, const char* dst){
		fComponents[src];
		fComponents[dst];
		fComponents.at(src)._connections[dst]=Connection(&fComponents.at(src), &fComponents.at(dst));
	}

	void connection_del(const char* src, const char* dst){
		if(!fComponents.count(src)) return;
		eraseKey(dst, fComponents.at(src)._connections);
	}

	void connection_command(const char* src, const char* dst){
		if(!fComponents.count(src)) return;
		if(!fComponents.at(src)._connections.count(dst)) return;
		fComponents.at(src)._connections.at(dst)._commandHeat=1.0f;
	}

	void connection_midi(const char* src, const char* dst){
		if(!fComponents.count(src)) return;
		if(!fComponents.at(src)._connections.count(dst)) return;
		fComponents.at(src)._connections.at(dst)._midiHeat=1.0f;
	}
}
