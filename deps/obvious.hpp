/*
obvious stuff
in the sense that you obviously want this
and it's obvious conceptually
but it's not necessarily obvious to make into convenient C++...
*/

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

template<typename T, typename U> std::vector<const T&> keys(const std::map<T, U>& map){
	std::vector<const T&> result;
	for(const auto& i: map) result.push_back(i.first);
	return result;
}

void replace(std::string& s, const std::string& a, const std::string& b){
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

template<typename T> void operator+=(std::set<T>& a, const std::set<T>& b){
	for(auto& i: b) a.insert(i);
}

#define OBVIOUS_MIN(X, Y) X=X<Y?X:Y
#define OBVIOUS_MAX(X, Y) X=X>Y?X:Y

#define OBVIOUS_TRANSFORM(CONTAINER, F, INITIAL)[&](decltype(CONTAINER) c){\
	auto r=INITIAL;\
	for(auto i=c.begin(); i!=c.end(); ++i) F;\
	return r;\
}(CONTAINER)

#define OBVIOUS_FILTER(CONTAINER, PREDICATE) OBVIOUS_TRANSFORM(CONTAINER, if(PREDICATE) r.push_back(*i), decltype(CONTAINER)())

struct Pair{ int x; int y; };

#define MAP_GET(M, I, D) (M.count(I)?M.at(I):D)
