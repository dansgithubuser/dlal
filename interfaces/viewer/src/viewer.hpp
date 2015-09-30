#include <SFML/Graphics.hpp>

#include <string>
#include <set>
#include <map>

class Component{
	public:
		Component();
		Component(std::string name);
		void render(sf::VertexArray&);
		std::string _name;
		std::set<Component*> _connections;
		//for layout
		int _lX, _lY;
		std::set<Component*> _lKnownConnections, _lKnownConnecters;
		bool _lLaidout;
};

class Viewer{
	public:
		Viewer();
		void process(std::string);
		void render(sf::RenderWindow&);
	private:
		void layout();
		sf::Font _font;
		std::map<std::string, Component> _nameToComponent;
		std::map<std::string, std::string> _variables;
		unsigned _w, _h;
};
