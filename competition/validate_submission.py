# competition/validate_submission.py

import pandas as pd
import sys
import numpy as np

from pathlib import Path
from PIL import Image

from metrics import (
    REQUIRED_COLUMNS,
    IMAGE_EXTENSIONS,
    CLASS_NAMES
)


def main(pred_path, test_images_dir):

    pred_path = Path(pred_path)
    test_images_dir = Path(test_images_dir)

    if not pred_path.exists():
        raise FileNotFoundError(
            f"Submission file not found: {pred_path}"
        )

    if not test_images_dir.exists():
        raise FileNotFoundError(
            f"Test images directory not found: {test_images_dir}"
        )

    # Read submission
    preds = pd.read_csv(pred_path)

    # Check required columns
    if list(preds.columns) != REQUIRED_COLUMNS:
        raise ValueError(
            f"Submission must contain exactly these columns: "
            f"{REQUIRED_COLUMNS}"
        )

    # Check image IDs
    if preds["image_id"].isna().any():
        raise ValueError("Missing image IDs found.")

    preds["image_id"] = preds["image_id"].astype(str)

    # Get available test images
    test_images = {
        path.name: path
        for path in test_images_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    }

    submitted_ids = set(preds["image_id"])
    available_ids = set(test_images.keys())

    # Check unknown images
    extra = submitted_ids - available_ids

    if extra:
        raise ValueError(
            f"Unknown image IDs found: {list(extra)[:5]}"
        )

    # Empty submissions are allowed if there are no detections.
    if preds.empty:
        print("VALID_SUBMISSION")
        return preds

    # Convert numeric columns
    numeric_columns = [
        "class_id",
        "x_min",
        "y_min",
        "x_max",
        "y_max",
        "confidence"
    ]

    for column in numeric_columns:
        preds[column] = pd.to_numeric(
            preds[column],
            errors="coerce"
        )

        if preds[column].isna().any():
            raise ValueError(
                f"Invalid or missing values in column: {column}"
            )

    # Check finite values
    if not np.isfinite(
        preds[numeric_columns].to_numpy(dtype=float)
    ).all():
        raise ValueError("Non-finite numeric values found.")

    # Validate each detection
    for _, row in preds.iterrows():

        image_id = row["image_id"]

        # Class ID must be an integer
        class_id = row["class_id"]

        if class_id != int(class_id):
            raise ValueError(
                f"Invalid class ID for image {image_id}."
            )

        class_id = int(class_id)

        if class_id not in CLASS_NAMES:
            raise ValueError(
                f"Unknown class ID {class_id} for image {image_id}."
            )

        # Confidence must be between 0 and 1
        confidence = row["confidence"]

        if not 0 <= confidence <= 1:
            raise ValueError(
                f"Invalid confidence score for image {image_id}."
            )

        # Get image dimensions
        with Image.open(test_images[image_id]) as image:
            image_width, image_height = image.size

        x_min = row["x_min"]
        y_min = row["y_min"]
        x_max = row["x_max"]
        y_max = row["y_max"]

        # Check bounding box coordinates
        if not (
            0 <= x_min < x_max <= image_width
            and 0 <= y_min < y_max <= image_height
        ):
            raise ValueError(
                f"Invalid bounding box for image {image_id}."
            )

    print("VALID_SUBMISSION")

    return preds


if __name__ == "__main__":

    if len(sys.argv) != 3:
        raise ValueError(
            "Usage: python validate_submission.py "
            "<predictions.csv> <test_images_directory>"
        )

    main(sys.argv[1], sys.argv[2])
