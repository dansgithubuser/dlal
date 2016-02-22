#include "vst.hpp"

#include <iostream>

int main(int argc, char** argv){
	dlalDyadInit();
	dlal::System system;
	dlal::Vst vst;
	dlal::Dummy dummy;
	if(argc<2||std::string(argv[1])=="-h"){
		std::cout<<"usage: vst <plugin>\n";
		dlalDyadShutdown();
		return 0;
	}
	system.set(22050, 10);
	std::cout<<system.add(vst, 0);
	std::cout<<system.add(dummy, 0);
	std::cout<<vst.connect(dummy);
	std::cout<<vst.command("load "+std::string(argv[1]))<<"\n";
	while(true){
		std::string s;
		std::cin>>s;
		if(s=="q") break;
		system.evaluate();
		std::cout<<system.report();
		for(unsigned i=0; i<dummy._audio.size(); ++i) std::cout<<dummy._audio[i]<<" ";
		std::cout<<"\n";
	}
	dlalDyadShutdown();
	return 0;
}
