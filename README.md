<h1 align="center">
  Object Detection Action
</h1>

<h4 align="center">Use YOLOS to get object detections</h4>

<p align="center">
  <img alt="Open Issues" src="https://img.shields.io/github/issues/aoxolotl/objdet_action">
</p>

Deploys [yolos-tiny](https://github.com/hustvl/YOLOS) by Hust Vision Lab as a
DataTorch action. Currently used for internal evaluation only.

## Quick Start

```yaml
name: Object Detector

triggers:
  # Adds a button to the annotator.
  annotatorButton:
    name: "Obj Det Whole File"
    icon: brain
    flow: whole-file
  # flow: 2-points

jobs:
  predict:
    # Properties about the trigger event can be accessed at 'event' property
    steps:
      - name: Download File
        action: datatorch/download-file@v1
        inputs:
          # Get the file id for the event that triggered this.
          fileId: ${{ event.fileId }}
          name: ${{ event.fileName }}

      - name: Predict BoundingBox
        action: aoxolotl/objdet_action@latest
        inputs:
          # Download file path from the previous action.
          imagePath: ${{ variable.path }}

          # Get the file id from action input
          fileId: ${{ event.fileId }}
          # Get the 2 points the user clicked
          # points: ${{ event.flowData.points }}

          # Annotation created by the four points. We will insert the
          # bounding box into this annotation
          annotationId: ${{ event.annotationId }}
```

> **NOTE:** Running this for the first time will take serval minutes to
> complete as it needs to download the model docker image. Do not exit out of
> your agent unless it specifically throws an error.

## Action

### Inputs

| Name           |  Type  |         Default          | Description                                                                                                                                                                            |
| -------------- | :----: | :----------------------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `imagePath`    | string |        _required_        | Absolute path to image. This path must be in the agent directory.                                                                                                                      |
| `points`       | array  |        _required_        | 4 points marking the most left, right, bottom and top points of the shape.                                                                                                             |
| `url`          | string | `http://localhost:3445`  | Url for sending requests. A docker image will be spun up on this port if not found.                                                                                              |
| `image`        | string | `add3000/objdet_server` | Docker image to spin up.                                                                                                                                                               |
| `annotationId` | string |          `null`          | Annotation to insert bbox into. If not provided the bbox will not be inserted.                                                                                         |

### Outputs

| Name           | Type  | Description                                |
| -------------- | :---: | ------------------------------------------ |
| `bboxes` | array | List of dictionaries contained lower left and upper right bounds|

