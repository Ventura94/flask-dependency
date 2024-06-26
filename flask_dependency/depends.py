from typing import Any, Callable, Optional

from flask import g


class Depends:
    def __init__(self, dependency: Optional[Callable[..., Any]] = None, cache: bool = True):
        self.dependency = dependency
        self.cache_key = f"_depends_cache_{id(dependency)}"
        self.cache = cache

    def __call__(self):
        if not hasattr(g, self.cache_key) or not self.cache:
            result = self.dependency()
            if hasattr(result, "__enter__") and hasattr(result, "__exit__"):
                with result as ctx_result:
                    setattr(g, self.cache_key, ctx_result)
                    return ctx_result
            setattr(g, self.cache_key, result)
            return result
        return getattr(g, self.cache_key)

    @classmethod
    def attach_dependency(cls, dependency_instance: Any) -> Any:
        instance = cls(type(dependency_instance))
        setattr(g, instance.cache_key, dependency_instance)
        return dependency_instance
