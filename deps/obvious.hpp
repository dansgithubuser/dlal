template<typename T, typename U> unsigned index(const T& value, const U& container){
	return std::find(container.begin(), container.end(), value)-container.begin();
}

template<typename T, typename U> bool in(const T& value, const U& container){
	return index(value, container)!=container.size();
}

