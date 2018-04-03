#include <dryad.hpp>
#include <page.hpp>
#include <wrapper.hpp>

#include <map>
#include <string>

#include <obvious.hpp>

static const int SZ=8;
static const int ADDABLES_WIDTH=12*SZ;

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

	Component& set(std::string name, std::string type, int x, int y, int* dx=nullptr, int* dy=nullptr){
		_name=name;
		_type=type;
		moveTo(x, y);
		_dx=dx; _dy=dy;
		return *this;
	}

	void dialpad(std::string pattern, sf::VertexArray& va, bool bright=false) const;

	void draw(sf::VertexArray& va, bool type=false){
		dans_sfml_wrapper_text_draw(
			mouseX()+2*SZ+2, mouseY(),
			SZ, _label.c_str(), 0, 128, 0, 255
		);
		if(type) dans_sfml_wrapper_text_draw(
			mouseX()+2*SZ+2, mouseY()+SZ,
			SZ, _type.c_str(), 0, 128, 0, 255
		);
		dialpad("79317", va);
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
			{"multiplier", "73-19"},
			{"network", "715893"},
			{"peak", "729"},
			{"raw", "713649"},
			{"sonic", "3197"},
			{"soundfont", "3187-28-56"},
			{"vst", "183"},
		};
		if(sketches.count(_type)) dialpad(sketches.at(_type), va, true);
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

	std::string _name;
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
	v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+SZ, _src->mouseY()+2*SZ), cn));//source
	if(_dst->_y>_src->_y){//destination below
		if(_dst->_y-_src->_y<=5*SZ){//directly below
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+SZ, _dst->mouseY()-SZ), cn));//drop to just above destination
		}
		else{
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()   , _src->mouseY()+3*SZ), cf));//diagonal
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()-SZ, _src->mouseY()+4*SZ), cf));//diagonal
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()-SZ, _dst->mouseY()-2*SZ), cf));//drop to just above destination
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()   , _dst->mouseY()-  SZ), cn));//diagonal
		}
	}
	else{
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+2*SZ, _src->mouseY()+3*SZ), cn));//diagonal
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+3*SZ, _src->mouseY()+2*SZ), cb));//diagonal
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+3*SZ, _dst->mouseY()     ), cb));//align vertically
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+2*SZ, _dst->mouseY()-  SZ), cn));//diagonal
	}
	v.push_back(sf::Vertex(sf::Vector2f(_dst->mouseX()+SZ, _dst->mouseY()-SZ), cn));//align horizontally
	v.push_back(sf::Vertex(sf::Vector2f(_dst->mouseX()+SZ, _dst->mouseY()   ), cn));//destination
	for(size_t i=0; i<v.size()-1; ++i){
		va.append(sf::Vertex(sf::Vector2f(v[i+0].position.x, v[i+0].position.y), v[i+0].color));
		va.append(sf::Vertex(sf::Vector2f(v[i+1].position.x, v[i+1].position.y), v[i+1].color));
	}
}

struct Variable: public Object {
	Variable(){}
	Variable(std::string name, std::string value):
		_name(name), _value(value) {}

	void draw() const;

	bool contains(int mouseX, int mouseY) const {
		return
			this->mouseX()<mouseX&&mouseX<this->mouseX()+dans_sfml_wrapper_text_width(SZ, text().c_str())
			&&
			this->mouseY()<mouseY&&mouseY<this->mouseY()+SZ;
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

template<typename K, typename V> struct DeleterMap: public std::map<K, V> {
	~DeleterMap(){ for(auto i: *this) delete i.second; }
};

dryad::Client* fClient=nullptr;
std::string fString;
std::string fText;
std::map<std::string, Variable> fVariables;
std::map<std::string, Component> fComponents;
Button fButtons[2];
std::vector<Object*> fSelected;
DeleterMap<std::string, dryad::Client*> fTies;
std::vector<Component> fAddables;
int fAddablesScrollX=0, fAddablesScrollY=0;

void Component::dialpad(std::string pattern, sf::VertexArray& va, bool bright) const {
	auto color=sf::Color(0, bright?255:64, in(this, fSelected)?255:0);
	for(size_t i=0; i<pattern.size()-1; ++i){
		if(pattern[i+1]=='-'){ ++i; continue; }
		int xi=(std::stoi(obvstr(pattern[i+0]))-1)%3;
		int yi=(std::stoi(obvstr(pattern[i+0]))-1)/3;
		int xf=(std::stoi(obvstr(pattern[i+1]))-1)%3;
		int yf=(std::stoi(obvstr(pattern[i+1]))-1)/3;
		va.append(sf::Vertex(sf::Vector2f(mouseX()+SZ*xi, mouseY()+SZ*yi), color));
		va.append(sf::Vertex(sf::Vector2f(mouseX()+SZ*xf, mouseY()+SZ*yf), color));
	}
}

void Variable::draw() const {
	dans_sfml_wrapper_text_draw(mouseX(), mouseY(), SZ, text().c_str(), 0, 255, in(this, fSelected)?255:0, 255);
}

Component* getSelectedComponent(){
	if(!fClient) throw std::logic_error("not initialized");
	Component* result;
	if(
		fSelected.size()!=1
		||
		!(result=dynamic_cast<Component*>(fSelected.at(0)))
	) return nullptr;
	return result;
}

extern "C" {
	void editor_init(const char* host, int port, const char* componentTypes){
		fClient=new dryad::Client(host, port);
		std::stringstream ss(componentTypes);
		std::string componentType;
		int y=SZ;
		while(ss>>componentType){
			fAddables.push_back(Component().set("", componentType, -ADDABLES_WIDTH, y, &fAddablesScrollX, &fAddablesScrollY));
			y+=4*SZ;
		}
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

	void editor_push(const char* command);

	void editor_button(int button, int pressed, int x, int y){
		if(button==0){
			if(pressed){
				fButtons[0].press(x, y);
				if(x>dans_sfml_wrapper_width()-ADDABLES_WIDTH){
					for(const auto& i: fAddables) if(i.contains(x, y)){
						editor_push(obvstr("queue_add ", i._type).c_str());
						break;
					}
				}
				else{
					std::vector<Object*> objects;
					for(auto& i: fComponents) objects.push_back(&i.second);
					for(auto& i: fVariables) objects.push_back(&i.second);
					for(auto i: objects) if(i->contains(x, y)&&!in(i, fSelected)){
						fSelected.push_back(i);
						break;
					}
				}
			}
			else fButtons[0].pressed=false;
		}
	}

	void editor_move(int x, int y){
		if(fButtons[0].pressed){
			int dx=fButtons[0].xTo(x);
			int dy=fButtons[0].yTo(y);
			if(x>dans_sfml_wrapper_width()-ADDABLES_WIDTH) fAddablesScrollY+=dy;
			else for(auto i: fSelected) i->moveBy(dx, dy);
		}
	}

	void editor_deselect(){ fSelected.clear(); }

	void editor_draw(){
		//clear
		gDansSfmlWrapperBoss->window.clear();
		//objects
		static sf::VertexArray va(sf::PrimitiveType::Lines);
		for(auto& i: fComponents) i.second.draw(va);
		//objects - addables
		fAddablesScrollX=dans_sfml_wrapper_width();
		for(auto& i: fAddables) i.draw(va, true);
		//objects - draw
		gDansSfmlWrapperBoss->window.draw(va, sf::RenderStates(sf::BlendMode(
			sf::BlendMode::Factor::One, sf::BlendMode::Factor::OneMinusSrcAlpha
		)));
		va.clear();
		//variables
		for(const auto& i: fVariables) i.second.draw();
		//text
		dans_sfml_wrapper_text_draw(SZ, gDansSfmlWrapperBoss->window.getSize().y-SZ, SZ, fText.c_str(), 255, 255, 255, 255);
		//display
		gDansSfmlWrapperBoss->window.display();
	}

	void editor_push(const char* command){
		auto component=getSelectedComponent();
		if(!component){
			for(auto& i: fComponents) if(
				i.second._type=="network"&&
				i.second._connections.size()==1&&
				i.second._connections.begin()->second._dst->_type=="commander"&&
				i.second._connections.begin()->second._dst->_connections.size()==0
			){
				component=&i.second;
				break;
			}
			if(!component){
				std::cerr<<"must select a single network component (couldn't find an appropriate one automatically)\n";
				return;
			}
		}
		if(component->_type!="network"){
			std::cerr<<"can only push to network components\n";
			return;
		}
		auto name=component->_name;
		if(!fTies.count(name))
			fTies[name]=new dryad::Client(fClient->ip(), std::stoi(fVariables.at(name+".port")._value));
		std::stringstream ss;
		dlal::Page(command, 0).toFile(ss);
		fTies.at(name)->writeSizedString(ss.str());
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
		fComponents[name].set(name, type, x, y);
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
