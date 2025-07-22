from inspect import signature
from types import UnionType
from typing import get_origin, get_args

from .depends import Depends


def inject(func):
    sig = signature(func)
    params = sig.parameters

    def wrapper(*args, **kwargs):
        for name, param in params.items():
            if isinstance(param.default, Depends):
                if param.default.dependency:
                    kwargs[name] = param.default()
                else:
                    if get_origin(param.annotation) is UnionType:
                        possible_types = get_args(param.annotation)
                    else:
                        possible_types = (param.annotation,)
                    if len(possible_types) == 1:
                        kwargs[name] = Depends(possible_types[0])()
                    else:
                        for dep_type in possible_types:
                            depends = Depends(dep_type)
                            if depends.exists():
                                kwargs[name] = depends()
                                break
        return func(*args, **kwargs)

    return wrapper
