# competition/metrics.py

IMAGE_HEIGHT = 416
IMAGE_WIDTH = 416

CLASS_NAMES = {
    0: "fire",
    1: "other",
    2: "smoke"
}

NUM_CLASSES = len(CLASS_NAMES)

REQUIRED_COLUMNS = [
    "image_id",
    "class_id",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "confidence"
]

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
}


def yolo_to_xyxy(class_id, center_x, center_y, width, height,
                 image_width, image_height):
    """
    Convert YOLO normalized bounding boxes to pixel coordinates.

    YOLO format:
    class_id, center_x, center_y, width, height

    Returns:
    class_id, x_min, y_min, x_max, y_max
    """

    x_min = (center_x - width / 2) * image_width
    y_min = (center_y - height / 2) * image_height

    x_max = (center_x + width / 2) * image_width
    y_max = (center_y + height / 2) * image_height

    # Clip coordinates to image boundaries
    x_min = max(0.0, min(x_min, image_width))
    y_min = max(0.0, min(y_min, image_height))

    x_max = max(0.0, min(x_max, image_width))
    y_max = max(0.0, min(y_max, image_height))

    return (
        int(class_id),
        float(x_min),
        float(y_min),
        float(x_max),
        float(y_max)
    )
