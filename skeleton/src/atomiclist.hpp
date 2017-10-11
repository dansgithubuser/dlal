#ifndef DLAL_ATOMIC_LIST_INCLUDED
#define DLAL_ATOMIC_LIST_INCLUDED

#include <atomic>
#include <stdexcept>
#include <vector>

namespace dlal{

/*
List with atomic mutation and iteration.

When an iterator is created, it will not be affected by mutations.
For example, this allows iterated reading in one thread while another assigns.

Note that iterators are distinct from lists.
Iterators will not interact safely with each other across threads.
*/
template <typename T> class AtomicList{
	private:
		struct Node{
			enum State{ FRESH, ACTIVE, DEAD };

			static void inc(Node* node){ if(node) ++node->_refs; }
			static void dec(Node* node){ if(node){
				if(node->_refs.fetch_sub(1)==1){
					node->_state=DEAD;
					dec(node->_next);
				}
			} }

			template <typename U> static void assign(U& a, Node* b){
				Node* oldA=a;
				a=b;
				inc(a);
				dec(oldA);
			}

			Node(): _refs(0), _state(FRESH) {}

			void activate(const T& value, Node* prev){
				_value=value;
				_prev=prev;
				_next=nullptr;
				inc(this);
				_state=ACTIVE;
			}
			void activate(const T& value, Node* prev, Node* next){
				_value=value;
				_prev=prev;
				_next=next;
				inc(this);
				_state=ACTIVE;
			}

			T _value;
			std::atomic<Node*> _prev, _next;
			std::atomic<int> _refs;
			std::atomic<State> _state;
		};

	public:
		class Iterator{
			friend class AtomicList;
			public:
				Iterator(): _head(nullptr) {}
				Iterator(const Iterator& other): _head(nullptr) { *this=other; }
				~Iterator(){ Node::dec(_head); }
				void operator++(){
					if(!_current) throw std::logic_error("AtomicList::Iterator out of bounds");
					_current=_current->_next;
				}
				bool operator!=(const Iterator& other) const { return _current!=other._current; }
				T& operator*() const { return _current->_value; }
				T* operator->() const { return &_current->_value; }
				void operator=(const Iterator& other){
					Node::assign(_head, other._head);
					_current=other._current;
				}
				operator bool() const { return _current; }
			private:
				Iterator(Node* head): _head(head), _current(head) { Node::inc(_head); }
				Iterator(Node* head, Node* current): _head(head), _current(current) { Node::inc(_head); }
				Node* _head;
				Node* _current;
		};

		AtomicList(): _head(nullptr) {}
		AtomicList(size_t size): _head(nullptr) { resize(size); }
		~AtomicList(){ for(auto i: _pool) delete i; }

		void operator=(const AtomicList& other)=delete;

		bool lockless() const {
			Node node;
			return
				_head.is_lock_free()
				&&
				node._next.is_lock_free()
				&&
				node._refs.is_lock_free()
				&&
				node._state.is_lock_free()
			;
		}

		void push_back(const T& value){
			insert(end(), value);
		}

		void insert(const Iterator iterator, const T& value){
			/*
			keep _head->prev pointing to tail
			this allows for tracking of tail without needing 2 atomics ops to mutate list
			*/
			Node* head=_head;
			Node* node;
			if(!head){
				node=getFreshNode();
				node->activate(value, nullptr);
				node->_prev=node;
				_head=node;
				return;
			}
			if(iterator._current==head){
				node=getFreshNode();
				node->activate(value, head->_prev, head);
				head->_prev=node;
				_head=node;
				return;
			}
			if(!iterator){
				Node* prev=head->_prev;
				Node* next=nullptr;
				node=getFreshNode();
				node->activate(value, prev, next);
				prev->_next=node;
				head->_prev=node;
			}
			else{
				Node* prev=iterator._current->_prev;
				Node* next=iterator._current;
				node=getFreshNode();
				node->activate(value, prev, next);
				prev->_next=node;
				next->_prev=node;
			}
		}

		void clear(){ Node::assign(_head, nullptr); }

		Iterator begin() const { return Iterator(_head); }
		Iterator end() const { return Iterator(nullptr, nullptr); }

		void resize(size_t size){
			auto oldSize=_pool.size();
			_pool.resize(size);
			for(auto i=oldSize; i<size; ++i) _pool[i]=new Node;
		}

		/*
		It's important that the iterating thread, not the mutating thread, be the one to finally end the use of nodes.
		Mutations flow from the mutation thread to the iterating thread in an atomic manner.
		However, deleting a node doesn't fall with the domain of atomic operations.
		If the mutating thread were allowed to delete nodes, there would be no way for iterating thread to know.
		At least, not a way I can think of that doesn't have a lock.
		So, mutating thread marks threads as dead and iterating thread frees them up.
		*/
		void freshen(){
			for(auto i: _pool) if(i->_state==Node::DEAD) i->_state=Node::FRESH;
		}

		void freshenFree(){
			for(auto i: _pool) if(i->_state==Node::DEAD) i->_value=T();
			freshen();
		}

		size_t poolSize() const { return _pool.size(); }

		int freshNodes() const {
			int result=0;
			for(auto i: _pool) if(i->_state==Node::FRESH) ++result;
			return result;
		}

	private:
		Node* getFreshNode(){
			for(auto i=0; i<_pool.size(); ++i){
				auto node=_pool[_poolIndex];
				if(node->_state==Node::FRESH) return node;
				++_poolIndex;
				_poolIndex%=_pool.size();
			}
			resize(_pool.size()*2+1);
			return getFreshNode();
		}

		std::atomic<Node*> _head;
		std::vector<Node*> _pool;
		size_t _poolIndex=0;
};

}//namespace dlal

#endif
