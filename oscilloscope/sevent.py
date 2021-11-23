"""
Taken from: https://github.com/Hikki12/sevent
"""

class Emitter:
    """This class implements a simple event emitter.
    
    Example usage::
        event = Emitter() 
        event.on('ready', callback)
        do_something()
        event.emit('ready', 'Finished!')
    """
    def __init__(self, *args, **kwargs):
        self.callback = None
        self.callbacks = {}

    def on(self, event_name, callback):
        """It sets the callback functions.
        :param event_name: str, name of the event
        :param callback: function
        """
        if self.callbacks is None:
            self.callbacks = {}
        if event_name not in self.callbacks:
            self.callbacks[event_name] = [callback]
        else:
            self.callbacks[event_name].append(callback)

    def emit(self, event_name, *args, **kwargs):
        """It emits an event, and calls the corresponding callback function.
        :param event_name: str, name of the event.
        """
        if self.callbacks is not None and event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                if callback.__code__.co_argcount > 0:
                    callback(*args, **kwargs)
                else:
                    callback()