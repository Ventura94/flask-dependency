from pydantic import BaseModel

from flask_dependency.validate_schema import validate_schema


class Model(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


def test_validate_schema_with_str():
    result = validate_schema(Model, '{"id": 1, "name": "test"}')
    assert isinstance(result, Model)


def test_validate_schema_with_dict():
    result = validate_schema(Model, {"id": 1, "name": "test"})
    assert isinstance(result, Model)


def test_validate_schema_with_orm():
    class ORM:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    result = validate_schema(Model, ORM(id=1, name="test"))
    assert isinstance(result, Model)
