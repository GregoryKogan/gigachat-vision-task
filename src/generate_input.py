import argparse
import logging
import os

from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_DATASET_NAME = "google-research-datasets/conceptual_captions"
DEFAULT_SPLIT = "train"
DEFAULT_IMG_URL_COLUMN = "image_url"

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")


def main() -> None:
    args = parse_args()

    logger.info(f"Starting generation. Target: {args.n} URLs from {args.dataset_name}")
    dataset = load_dataset(args.dataset_name, split=args.split, streaming=True)

    dataset = dataset.select_columns([args.img_url_column])
    dataset = dataset.rename_column(args.img_url_column, "img_url")
    dataset = dataset.filter(is_valid_url)
    dataset = dataset.take(args.n)

    output_dir = os.path.dirname(args.output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    dataset.to_csv(args.output_path, index=False)
    logger.info(f"Successfully saved {args.n} URLs to {args.output_path}")


def is_valid_url(x: dict) -> bool:
    return x.get("img_url") and x.get("img_url").lower().endswith(VALID_EXTENSIONS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate input image URLs")
    parser.add_argument(
        "--n", type=int, required=True, help="Number of URLs to collect"
    )
    parser.add_argument(
        "--output-path", type=str, required=True, help="Path to output CSV file"
    )
    parser.add_argument(
        "--dataset-name", type=str, default=DEFAULT_DATASET_NAME, help="HF Dataset name"
    )
    parser.add_argument(
        "--split", type=str, default=DEFAULT_SPLIT, help="Dataset split"
    )
    parser.add_argument(
        "--img-url-column",
        type=str,
        default=DEFAULT_IMG_URL_COLUMN,
        help="Column name containing URL",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
