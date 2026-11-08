# competition/evaluate.py

import pandas as pd
import sys

from pathlib import Path
from PIL import Image

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

from metrics import (
    CLASS_NAMES,
    IMAGE_EXTENSIONS,
    yolo_to_xyxy
)

from validate_submission import main as validate_submission


def load_ground_truth(test_images_dir, test_labels_dir):

    test_images_dir = Path(test_images_dir)
    test_labels_dir = Path(test_labels_dir)

    coco = COCO()

    images = []
    annotations = []

    annotation_id = 1

    image_paths = sorted([
        path for path in test_images_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ])

    for image_id, image_path in enumerate(image_paths, start=1):

        with Image.open(image_path) as image:
            image_width, image_height = image.size

        images.append({
            "id": image_id,
            "file_name": image_path.name,
            "width": image_width,
            "height": image_height
        })

        label_path = test_labels_dir / f"{image_path.stem}.txt"

        if not label_path.exists():
            raise FileNotFoundError(
                f"Ground-truth label not found: {label_path}"
            )

        with label_path.open("r", encoding="utf-8") as file:

            for line in file:

                values = line.strip().split()

                if not values:
                    continue

                if len(values) != 5:
                    raise ValueError(
                        f"Invalid YOLO annotation in {label_path.name}"
                    )

                class_id, center_x, center_y, width, height = (
                    float(value) for value in values
                )

                if (
                    not all(
                        map(
                            lambda value: value == value
                            and abs(value) != float("inf"),
                            [class_id, center_x, center_y, width, height]
                        )
                    )
                    or class_id != int(class_id)
                    or int(class_id) not in CLASS_NAMES
                    or not (
                        0 <= center_x <= 1
                        and 0 <= center_y <= 1
                        and 0 < width <= 1
                        and 0 < height <= 1
                    )
                ):
                    raise ValueError(
                        f"Invalid annotation in {label_path.name}"
                    )

                (
                    class_id,
                    x_min,
                    y_min,
                    x_max,
                    y_max
                ) = yolo_to_xyxy(
                    class_id,
                    center_x,
                    center_y,
                    width,
                    height,
                    image_width,
                    image_height
                )

                box_width = x_max - x_min
                box_height = y_max - y_min

                if box_width <= 0 or box_height <= 0:
                    continue

                annotations.append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": class_id + 1,
                    "bbox": [
                        x_min,
                        y_min,
                        box_width,
                        box_height
                    ],
                    "area": box_width * box_height,
                    "iscrowd": 0
                })

                annotation_id += 1

    categories = [
        {
            "id": class_id + 1,
            "name": class_name
        }
        for class_id, class_name in CLASS_NAMES.items()
    ]

    coco.dataset = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    coco.createIndex()

    # Map image filenames to COCO image IDs
    image_id_map = {
        image["file_name"]: image["id"]
        for image in images
    }

    return coco, image_id_map, images


def load_predictions(preds, image_id_map):

    results = []

    for _, row in preds.iterrows():

        image_id = image_id_map[row["image_id"]]

        x_min = float(row["x_min"])
        y_min = float(row["y_min"])
        x_max = float(row["x_max"])
        y_max = float(row["y_max"])

        results.append({
            "image_id": image_id,
            "category_id": int(row["class_id"]) + 1,
            "bbox": [
                x_min,
                y_min,
                x_max - x_min,
                y_max - y_min
            ],
            "score": float(row["confidence"])
        })

    return results


def main(pred_path, test_images_dir, test_labels_dir):

    # Validate submission
    preds = validate_submission(
        pred_path,
        test_images_dir
    )

    # Load ground-truth annotations
    coco_gt, image_id_map, images = load_ground_truth(
        test_images_dir,
        test_labels_dir
    )

    # Load predictions
    results = load_predictions(
        preds,
        image_id_map
    )

    # Create COCO prediction object
    if results:

        coco_dt = coco_gt.loadRes(results)

    else:

        # Handle submissions with no detections
        coco_dt = COCO()

        coco_dt.dataset = {
            "images": images,
            "annotations": [],
            "categories": coco_gt.dataset["categories"]
        }

        coco_dt.createIndex()

    # Run COCO evaluation
    evaluator = COCOeval(
        coco_gt,
        coco_dt,
        iouType="bbox"
    )

    evaluator.params.iouThrs = [
        0.50, 0.55, 0.60, 0.65, 0.70,
        0.75, 0.80, 0.85, 0.90, 0.95
    ]

    evaluator.params.maxDets = [1, 10, 100]

    evaluator.evaluate()
    evaluator.accumulate()
    evaluator.summarize()

    # Primary metric: mAP@50:95
    final_score = float(evaluator.stats[0])

    print(f"SCORE={final_score:.8f}")


if __name__ == "__main__":

    if len(sys.argv) != 4:
        raise ValueError(
            "Usage: python evaluate.py "
            "<predictions.csv> "
            "<test_images_directory> "
            "<test_labels_directory>"
        )

    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3]
    )
