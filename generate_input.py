import datasets
import pandas as pd
import argparse
import csv


DEFAULT_DATASET_NAME = "google-research-datasets/conceptual_captions"
DEFAULT_SPLIT = "train"
DEFAULT_IMG_URL_COLUMN = "image_url"


def main():
    args = parse_args()
    img_urls = load_img_urls(args.dataset_name, args.split, args.img_url_column)
    random_img_urls = select_random_img_urls(img_urls, args.n)
    save_img_urls(random_img_urls, args.output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n", type=int, required=True, help="Number of random image URLs to save"
    )
    parser.add_argument(
        "--output-path", type=str, required=True, help="Output txt file path"
    )
    parser.add_argument(
        "--dataset-name", type=str, default=DEFAULT_DATASET_NAME, help="Dataset name"
    )
    parser.add_argument("--split", type=str, default=DEFAULT_SPLIT, help="Split")
    parser.add_argument(
        "--img-url-column",
        type=str,
        default=DEFAULT_IMG_URL_COLUMN,
        help="Image URL column",
    )
    return parser.parse_args()


def load_img_urls(dataset_name: str, split: str, img_url_column: str) -> pd.Series:
    df = datasets.load_dataset(dataset_name, split=split).to_pandas()
    return df[img_url_column]


def select_random_img_urls(img_urls: pd.Series, n: int) -> pd.Series:
    return img_urls.sample(n)


def save_img_urls(img_urls: pd.Series, path: str) -> None:
    with open(path, "w") as f:
        f.writelines(map(lambda x: x + "\n", img_urls.tolist()))


if __name__ == "__main__":
    main()
