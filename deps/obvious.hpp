/*
obvious stuff
in the sense that you obviously want this
and it's obvious conceptually
but it's not necessarily obvious to make into convenient C++...
*/

#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#define OBVIOUS_LOUD(X)\
	std::cout<<"/===="<<#X<<"====\\\n";\
	std::cout<<X<<"\n";\
	std::cout<<"\\===="<<#X<<"====/\n";

template<typename T, typename U> unsigned index(const T& value, const U& container){
	return std::find(container.begin(), container.end(), value)-container.begin();
}

template<typename T, typename U> bool in(const T& value, const U& container){
	return index(value, container)!=container.size();
}

template<typename T, typename U> void erase(const T& value, U& container){
	container.erase(std::find(container.begin(), container.end(), value));
}

template<typename T, typename U> std::vector<const T&> keys(const std::map<T, U>& map){
	std::vector<const T&> result;
	for(const auto& i: map) result.push_back(i.first);
	return result;
}

static void replace(std::string& s, const std::string& a, const std::string& b){
	size_t i=0;
	while(true){
		i=s.find(a, i);
		if(i==std::string::npos) break;
		s.replace(i, a.size(), b);
		i+=b.size();
	}
}

template<typename T> std::ostream& streamContainer(std::ostream& o, const T& t, std::string prefix){
	//figure out if big or not
	bool big=false;
	{
		std::stringstream ss;
		for(const auto& i: t) ss<<i<<", ";
		if(in('\n', ss.str())||ss.str().size()>72) big=true;
	}
	//meat
	o<<prefix<<"{";
	if(big) o<<"\n";
	bool first=true;
	for(const auto& i: t){
		if(!big&&!first) o<<", ";
		first=false;
		std::stringstream ss;
		ss<<i;
		std::string s=ss.str();
		if(big){
			s="\t"+s;
			replace(s, "\n", "\n\t");
		}
		o<<s;
		if(big) o<<",\n";
	}
	o<<"}";
	return o;
}

template<typename T> std::ostream& operator<<(std::ostream& o, const std::vector<T>& c){
	return streamContainer(o, c, "v");
}

template<typename T> std::ostream& operator<<(std::ostream& o, const std::set<T>& c){
	return streamContainer(o, c, "s");
}

template<typename T, typename U> struct KeyValuePair{
	KeyValuePair(const T& t, const U& u): key(t), value(u) {}
	const T& key;
	const U& value;
};
template<typename T, typename U> std::ostream& operator<<(std::ostream& o, const KeyValuePair<T, U>& p){
	return o<<p.key<<": "<<p.value;
}

template<typename T, typename U> std::ostream& operator<<(std::ostream& o, const std::map<T, U>& c){
	std::vector<KeyValuePair<T, U>> x;
	for(const auto& i: c) x.push_back(KeyValuePair<T, U>(i.first, i.second));
	return streamContainer(o, x, "m");
}

template<typename T, typename U> std::ostream& operator<<(std::ostream& o, const std::pair<T, U>& p){
	o<<"("<<p.first<<", "<<p.second<<")";
	return o;
}

#define OBVIOUS_PLUS_EQUALS_BASE(CONTAINER1, CONTAINER2, F)\
	template<typename T> void operator+=(CONTAINER1<T>& r, const CONTAINER2<T>& a){\
		for(auto& i: a) F;\
	}

#define OBVIOUS_PLUS_EQUALS_SET(CONTAINER)\
	OBVIOUS_PLUS_EQUALS_BASE(std::set, CONTAINER, r.insert(i))

#define OBVIOUS_PLUS_EQUALS_VECTOR(CONTAINER)\
	OBVIOUS_PLUS_EQUALS_BASE(std::vector, CONTAINER, r.push_back(i))

#define OBVIOUS_PLUS_EQUALS(CONTAINER)\
	OBVIOUS_PLUS_EQUALS_SET(CONTAINER)\
	OBVIOUS_PLUS_EQUALS_VECTOR(CONTAINER)

OBVIOUS_PLUS_EQUALS(std::set)
OBVIOUS_PLUS_EQUALS(std::vector)

#define OBVIOUS_MIN(X, Y) (X<Y?X:Y)
#define OBVIOUS_MAX(X, Y) (X>Y?X:Y)

#define OBVIOUS_MINI(X, Y) X=OBVIOUS_MIN(X, Y)
#define OBVIOUS_MAXI(X, Y) X=OBVIOUS_MAX(X, Y)

#define OBVIOUS_TRANSFORM(CONTAINER, F, INITIAL)[&](){\
	auto r=INITIAL;\
	for(auto i=CONTAINER.begin(); i!=CONTAINER.end(); ++i) F;\
	return r;\
}()

#define OBVIOUS_BINARY_TRANSFORM(CONTAINER, F, INITIAL)[&](){\
	auto r=INITIAL;\
	auto a=CONTAINER.end();\
	for(auto b=CONTAINER.begin(); b!=CONTAINER.end(); ++b){\
		if(a!=CONTAINER.end()) F;\
		a=b;\
	}\
	return r;\
}()

struct Pair{
	Pair(int x, int y): x(x), y(y) {}
	bool operator<(const Pair& other) const{
		if(x<other.x) return true;
		if(x>other.x) return false;
		if(y<other.y) return true;
		return false;
	}
	int x, y;
};

static std::ostream& operator<<(std::ostream& o, const Pair& p){
	return o<<"("<<p.x<<", "<<p.y<<")";
}

#define MAP_GET(M, I, D) (M.count(I)?M.at(I):D)

#define OBVIOUS_IF(PREDICATE, ACTION) (PREDICATE?((ACTION), 0):0)
