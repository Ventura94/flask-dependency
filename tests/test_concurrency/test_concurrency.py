from concurrent.futures import Future

import httpx
from flask import Flask, Blueprint

from flask_dependency import BackgroundTask
from flask_dependency import Depends
from flask_dependency import route


def test_run_background_task():
    background_task = BackgroundTask(max_workers=2)

    def sample_task(duration):
        import time
        time.sleep(duration)
        return f"Slept for {duration} seconds"

    future = background_task.run(sample_task, 1)
    assert isinstance(future, Future)
    result = future.result(timeout=2)
    assert result == "Slept for 1 seconds"


def test_background_task_flask_integration():
    app = Flask(__name__)
    blueprint = Blueprint("test_blueprint", __name__)
    app.debug = True

    def sample_task(duration):
        import time
        time.sleep(duration)
        return f"Slept for {duration} seconds"

    @route(blueprint, "/test", methods=["POST"], endpoint="route_test")
    def route_test(background_task: BackgroundTask = Depends()):
        future = background_task.run(sample_task, 1)
        assert isinstance(future, Future)
        result = future.result(timeout=2)
        assert result == "Slept for 1 seconds"
        return {"message": "success"}

    app.register_blueprint(blueprint)

    with httpx.Client(app=app, base_url="http://testserver") as client:
        response = client.post("/test", json='{"id": 1, "name": "test"}')
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
