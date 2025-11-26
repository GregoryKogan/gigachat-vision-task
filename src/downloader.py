import argparse
import asyncio
import csv
import hashlib
import logging
import os
from typing import Iterator

import aiofiles
import aiohttp
from tqdm.asyncio import tqdm

MAX_CONCURRENT_DOWNLOADS = 32
TIMEOUT = 8  # seconds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("downloader.log")],
)
logger = logging.getLogger(__name__)


def main() -> None:
    args = parse_args()
    urls = read_input_urls(args.input_urls_path)
    asyncio.run(download_images(urls, args.output_dir))


def read_input_urls(file_path: str) -> Iterator[str]:
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            yield row[0]


async def download_images(urls: Iterator[str], output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async with aiohttp.ClientSession() as session:
        tasks = [download_image(url, output_dir, session, semaphore) for url in urls]
        results = await tqdm.gather(*tasks, desc="Downloading images")

    logger.info(f"Successfully downloaded {sum(results)}/{len(tasks)} images")
    print(f"Successfully downloaded {sum(results)}/{len(tasks)} images")


async def download_image(
    url: str,
    output_dir: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
) -> bool:
    file_path = os.path.join(output_dir, calculate_file_name(url))
    if os.path.exists(file_path):
        logger.info(f"Image already exists: {file_path}")
        return True

    try:
        async with semaphore:
            async with session.get(url, timeout=TIMEOUT) as response:
                validate_response(response)

                content = await response.read()
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
                logger.info(f"Downloaded image to {file_path}")
                return True

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning(f"Failed to download image from {url}: {e.__class__.__name__}")
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
    return False


def calculate_file_name(url: str) -> str:
    hash_digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    extension = url.split("?")[0].split(".")[-1]
    return f"{hash_digest}.{extension}"


def validate_response(response: aiohttp.ClientResponse) -> None:
    validate_http_status(response)
    validate_content_type(response)


def validate_http_status(response: aiohttp.ClientResponse) -> None:
    if response.status != 200:
        raise Exception(f"HTTP status {response.status} for {response.url}")


def validate_content_type(response: aiohttp.ClientResponse) -> None:
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise Exception(f"Invalid content type: {content_type} for {response.url}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download images from URLs")
    parser.add_argument(
        "--input-urls-path", type=str, required=True, help="Path to input URLs CSV file"
    )
    parser.add_argument(
        "--output-dir", type=str, required=True, help="Path to output directory"
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
