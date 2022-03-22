from typing import Any


class Singleton(object):
    def __init__(self, decorated: object) -> None:
        self._decorated = decorated

    def instance(self, *args, **kwargs):
        try:
            return self.__instance
        except AttributeError:
            self.__instance = self._decorated(*args, **kwargs)
            return self.__instance

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        raise TypeError('Singletons must be accesses through `instance()`!')

    def __instancecheck__(self, __instance: Any) -> bool:
        return isinstance(__instance, self._decorated)

