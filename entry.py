import os
import time
import requests
import docker
from requests.exceptions import HTTPError

import numpy as np
import shapely.ops
from urllib.parse import urlparse
from shapely import geometry
from typing import List, Tuple
from docker.models.resource import Model

from datatorch import get_input, agent, set_output
from datatorch.api.entity.sources.image import BoundingBox

Point = Tuple[float, float]

directory = os.path.dirname(os.path.abspath(__file__))

agent_dir = agent.directories().root
points = get_input("points")
image_path = get_input("imagePath")
address = urlparse(get_input("url"))
image = get_input("image")
annotation = get_input("annotation")
annotation_id = None
if annotation:
    annotation_id = annotation.get("id")
label_id = get_input("labelId")
file_id = get_input("fileId")

# [[10,20],[30, 40],[50,60],[70,80]]
# points: List[Point] = [(10.0, 20.0), (30.0, 40.0), (50.0, 60.0), (70.0, 80.0)]
# image_path = "/home/desktop/.config/datatorch/agent/temp/download-file/20201025_102443 (17th copy).jpg"

CONTAINER_NAME = "datatorch-objdet-action"

def valid_image_path():
    if not image_path.startswith(agent_dir):
        print(f"Directory must be inside the agent folder ({agent_dir}).")
        exit(1)

    if not os.path.isfile(image_path):
        print(f"Image path must be a file ({image_path}).")
        exit(1)

def return_container_status(container_name: str) -> str:
    """Get the status of a container by it's name

    :param container_name: the name of the container
    :return: string
    """
    # Connect to Docker using the default socket or the configuration
    # in your environment
    docker_client = docker.from_env()

    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound as exc:
        print(f"Check container name!\n{exc.explanation}")
        return "EEXIST"
    else:
        container_state = container.attrs["State"]
        return container_state["Status"]

def start_server(port: int) -> None:
    docker_client = docker.from_env()
    # only start server if it image is not up already exist
    if return_container_status(CONTAINER_NAME) != "running":
        print(f"Creating {CONTAINER_NAME} container on port {port}.")
        print(
            f"Downloading {image} docker image. This may take a few mins.", flush=True
        )
        container = docker_client.containers.run(
            image,
            detach=True,
            ports={"8000/tcp": port},
            restart_policy={"Name": "always"},
            volumes={agent_dir: {"bind": "/agent", "mode": "rw"}},
            name=CONTAINER_NAME,
        )
        if isinstance(container, Model):
            print(f"Created Container ({container.short_id}).")
    else:
        print(f"Container {CONTAINER_NAME} already running")
        print(f"Sleeping to wait for server bring up")
    time.sleep(20)


def call_model(path: str, points: List[Point], address: str) -> List[List[Point]]:
    agent_folder = agent.directories().root
    container_path = path.replace(agent_folder, "/agent")

    print(f"Sending request to '{address}' (POST)")
    print(f"Image Path = {path}")
    print(f"Container Path = {container_path}")
    print(f"Points = {points}")

    response = requests.post(address, 
                             json={"path": container_path, "points": points},
                             timeout=20
                            )
    response.raise_for_status()
    json = response.json()
    return json["bboxes"]


def send_request(annotation_id=None):
    attempts = 0

    start_server(address.port or 80)

    while True:
        try:
            attempts += 1
            print(f"Attempt {attempts}: Request to Segformer Server")
            bboxes = call_model(image_path, points, address.geturl())
            for bbox in bboxes:
                # Create a bounding box object
                b = BoundingBox()

                # use a from_bbox method
                # handles merging or creating annotations internally
                top_left = (bbox["xmin"], bbox["ymin"])
                bottom_right = (bbox["xmax"], bbox["ymax"])
                b.create_bbox_from_points(top_left, bottom_right, 
                                          annotation, 
                                          label_id, file_id)

            exit(0)

        except HTTPError as http_err:
            print(http_err)
            print(f"Attempt {attempts}: Could not connect to model.")
            if attempts > 5:
                break
            start_server(address.port or 80)
        except Exception as ex:
            print("Exception", ex, flush=True)
            break

    print("Could not send request.")
    exit(1)


if __name__ == "__main__":
    valid_image_path()
    send_request(annotation_id=annotation_id)
