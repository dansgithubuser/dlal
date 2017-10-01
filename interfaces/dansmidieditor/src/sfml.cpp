#include <courierCode.hpp>
#include <keys.hpp>

#include <SFML/Graphics.hpp>

#include <string>
#include <sstream>

struct Boss{
	int init(int width, int height, const char* title){
		if(!font.loadFromMemory(courierCode, courierCodeSize)) return 1;
		window.create(sf::VideoMode(width, height), title);
		window.setKeyRepeatEnabled(false);
		va.setPrimitiveType(sf::PrimitiveType::Triangles);
		return 0;
	}

	const char* pollEvent(){
		std::stringstream ss;
		sf::Event event;
		if(window.pollEvent(event)){
			switch(event.type){
				case sf::Event::KeyPressed:
				case sf::Event::KeyReleased:
					if(event.key.code==sf::Keyboard::Key::Unknown) break;
					ss<<(event.type==sf::Event::KeyPressed?"<":">")
						<<keys[event.key.code];
					break;
				case sf::Event::MouseMoved:
					ss<<"x"<<event.mouseMove.x<<"y"<<event.mouseMove.y;
					break;
				case sf::Event::MouseButtonPressed:
				case sf::Event::MouseButtonReleased:
					ss<<"b"<<(event.type==sf::Event::MouseButtonPressed?"<":">")
						<<event.mouseButton.button
						<<"x"<<event.mouseButton.x<<"y"<<event.mouseButton.y;
					break;
				case sf::Event::MouseWheelMoved:
					ss<<"w"<<event.mouseWheel.delta;
					break;
				case sf::Event::Closed:
					ss<<"q";
					break;
				default: break;
			}
		}
		result=ss.str();
		return result.c_str();
	}

	sf::RenderWindow window;
	sf::Font font;
	sf::VertexArray va;
	std::string result;
};

Boss* fBoss=nullptr;

extern "C" {
	int init(int width, int height, const char* title){
		if(fBoss) delete fBoss;
		fBoss=new Boss;
		return fBoss->init(width, height, title);
	}

	const char* poll_event(){ return fBoss->pollEvent(); }

	void vertex(int x, int y, int r, int g, int b, int a){
		fBoss->va.append(sf::Vertex(
			sf::Vector2f(x, y),
			sf::Color(r, g, b, a)
		));
	}

	int width(){ return fBoss->window.getSize().x; }

	int height(){ return fBoss->window.getSize().y; }

	void display(){
		fBoss->window.draw(fBoss->va);
		fBoss->window.display();
		fBoss->va.clear();
	}
}
