class Event:

    _events = {}

    def trigger_event(self,tag,*args,**kwargs):
        if tag in Event._events:
            _answers = []
            for _handler in Event._events[tag]:
                _answers.append(_handler(*args,**kwargs))
            return _answers

    def event(tag=None):
        def _wrapper(func):
            if tag:
                if not tag in Event._events:
                    Event._events[tag] = []
                Event._events[tag].append(func)
            return func
        return _wrapper