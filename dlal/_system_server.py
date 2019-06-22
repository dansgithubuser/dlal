import collections
import json
import uuid
import weakref

FREE = uuid.uuid4()

_Root = collections.namedtuple('_Root', 'system skeleton free')

class SystemServer:
    def __init__(self, system):
        from . import skeleton
        self.root = _Root(
            weakref.proxy(system),
            skeleton,
            lambda: FREE,
        )
        self.store = {}

    def handle_request(self, request):
        request = json.loads(request)
        value = self.root
        for i, v in enumerate(request['path']):
            if i == 0 and v in self.store:
                value = self.store[v]
            else:
                value = getattr(value, v)
        args = [self.sub(i) for i in request.get('args', [])]
        kwargs = {k: self.sub(v) for k, v in request.get('kwargs', {}).items()}
        if callable(value):
            result = value(*args, **kwargs)
        else:
            result = value
        if request.get('op') == 'store':
            if result == FREE:
                del self.store[request['uuid']]
            else:
                self.store[request['uuid']] = result
                response = json.dumps(request)
        else:
            request['result'] = result
            response = json.dumps(request)
        return response

    def sub(self, arg):
        return self.store.get(arg, arg)
