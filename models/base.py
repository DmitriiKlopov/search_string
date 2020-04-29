from typing import (
    Any,
    Dict,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel as _BaseModel, create_model


if TYPE_CHECKING:
    Model = TypeVar("Model", bound="BaseModel")
    TupleStr = Tuple[str, ...]

    _partial_models_cache: Dict[Tuple[Type[Model], str, TupleStr], Type[Model]]

_partial_models_cache = {}


class Partial:
    pass


class BaseModel(_BaseModel):
    def __class_getitem__(
        cls: Type["Model"], item: Union[Type[Any], Tuple[Type[Any], ...]]
    ) -> Type["Model"]:
        if item is Partial:
            return create_partial(cls)
        return cls

    @classmethod
    def partial(
        cls: Type["Model"], *field_names: str, name: Optional[str] = None
    ) -> Type["Model"]:
        return create_partial(cls, *field_names, name=name)


def create_partial(
    model: Type["Model"], *field_names: str, name: Optional[str] = None
) -> Type["Model"]:
    if name is None:
        name = f"{model.__name__}Partial"

    if not field_names:
        field_names = model.__fields__.keys()

    cache_key = (model, name, tuple(sorted(field_names)))
    new_model = _partial_models_cache.get(cache_key)
    if new_model is not None:
        return new_model

    new_model = create_model(name, __base__=model, __module__=model.__module__)
    for fn in field_names:
        field = new_model.__fields__.get(fn)
        if field is not None and field.required:
            field.allow_none = field.required = False

    _partial_models_cache[cache_key] = new_model
    return new_model
