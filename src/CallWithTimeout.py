import threading
from typing import Callable


class TimeoutExeption(Exception):
    pass


class SharedObject(object):
    response = None


class _Executor(threading.Thread):

    def __init__(self, shared: SharedObject, toExecute: Callable, args: tuple):
        super(_Executor, self).__init__()
        self.to_execute = toExecute
        self.args = args
        self.shared = shared

    def run(self):
        self.shared.response = self.to_execute(*self.args)


class ExecutorWithTimeout:
    shared_obj = SharedObject()

    def callWithTimeout(self, timeout_sec: int, callable: Callable, args: tuple):
        if timeout_sec <= 0:
            raise Exception("timeout_sec too short")
        process = _Executor(self.shared_obj, callable, args)
        process.start()
        # Esperar el tiempo de timeout
        process.join(timeout_sec)

        if process.is_alive():
            raise TimeoutExeption('TimeOut')
        else:
            return self.shared_obj.response
