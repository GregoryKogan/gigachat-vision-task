import argparse
from datasets import load_dataset


DEFAULT_DATASET_NAME = "google-research-datasets/conceptual_captions"
DEFAULT_SPLIT = "train"
DEFAULT_IMG_URL_COLUMN = "image_url"


def main() -> None:
    args = parse_args()

    dataset = load_dataset(args.dataset_name, split=args.split, streaming=True)
    dataset = dataset.select_columns([args.img_url_column])
    dataset = dataset.rename_column(args.img_url_column, "img_url")
    dataset = dataset.take(args.n)
    dataset.to_csv(args.output_path, index=False)


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
