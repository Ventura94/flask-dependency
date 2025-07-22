import random
from contextlib import contextmanager

import httpx
from flask import Flask, Blueprint
from pydantic import BaseModel

from flask_dependency import Depends
from flask_dependency import FormModel
from flask_dependency import route
from flask_dependency.exceptions.unprocessable_content import (
    UnprocessableContent,

)
from flask_dependency.inject import inject


def handle_unprocessable_content(exception: UnprocessableContent):
    return {
        "message": exception.message,
        "errors": exception.error_details,
    }, exception.status_code


class InputModelForm(FormModel):
    id: int
    name: str


class ResponseSchema(BaseModel):
    message: str

    class Config:
        orm_mode = True


def test_route_with_input_schema():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)
    app.debug = True

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(input_data: InputModelForm = Depends()):
        assert input_data.id == 1
        assert input_data.name == "test"
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_route_without_input_schema():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)

    @route(blueprint, "/test", methods=["GET"], endpoint="route_test")
    def route_test():
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_route_with_input_schema_and_response_schema():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)

    @route(
        blueprint,
        "/test",
        methods=["POST"],
        response_schema=ResponseSchema,
        endpoint="route_test",
    )
    def route_test(input_data: InputModelForm = Depends()):
        assert input_data.id == 1
        assert input_data.name == "test"
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_route_with_invalid_input_schema():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)
    app.register_error_handler(UnprocessableContent, handle_unprocessable_content)

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(input_data: InputModelForm = Depends()):
        assert input_data.id == 1
        assert input_data.name == "test"
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1}')
        assert response.status_code == 422
        assert response.json() == {
            "errors": ["name field required"],
            "message": "Invalid Input Data",
        }


def dependency():
    return "test dependency"


def test_route_with_dependency_injections():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)
    app.register_error_handler(UnprocessableContent, handle_unprocessable_content)

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(
            input_data: InputModelForm = Depends(InputModelForm),
            test_depends: str = Depends(dependency),
    ):
        assert input_data.id == 1
        assert input_data.name == "test"
        assert test_depends == dependency()
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


@contextmanager
def context_dependency():
    yield "test dependency"


def test_route_with_dependency_context_manager_injections():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)
    app.register_error_handler(UnprocessableContent, handle_unprocessable_content)
    app.debug = True

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(
            input_data: InputModelForm = Depends(InputModelForm),
            test_depends: str = Depends(context_dependency),
    ):
        assert input_data.id == 1
        assert input_data.name == "test"
        assert test_depends == dependency()
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def random_dependency():
    return random.randint(0, 100)


def test_route_with_dependency_cache_prove():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)
    app.register_error_handler(UnprocessableContent, handle_unprocessable_content)
    app.debug = True

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(
            input_data: InputModelForm = Depends(InputModelForm),
            random_depends_one: int = Depends(random_dependency),
            random_depends_two: int = Depends(random_dependency),
    ):
        assert input_data.id == 1
        assert input_data.name == "test"
        assert random_depends_one == random_depends_two  # I check that the dependency cache works
        return {"random": random_depends_one}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        random_one = response.json()["random"]
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        random_two = response.json()["random"]
        assert random_one != random_two  # I check that the cache does not work between requests


def test_route_with_dependency_injections_unions():
    app = Flask(__name__)
    app.debug = True
    blueprint = Blueprint("test_blueprint", __name__)
    app.register_error_handler(UnprocessableContent, handle_unprocessable_content)

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(
            input_data: InputModelForm = Depends(),
            test_depends: str = Depends(dependency),
    ):
        @inject
        def test_unions(input_data: InputModelForm | ResponseSchema = Depends()):
            assert isinstance(input_data, InputModelForm)

        test_unions()

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
