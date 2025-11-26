import argparse
import logging
import math
import os
from glob import glob
from typing import Optional, Tuple

import torch
from diffusers import (
    EulerAncestralDiscreteScheduler,
    StableDiffusionInstructPix2PixPipeline,
)
from PIL import Image
from tqdm import tqdm

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/edit_images.log")],
)
logger = logging.getLogger(__name__)


class ImageEditor:
    def __init__(self, model: str):
        self.device, self.dtype = self._get_device_and_dtype()
        logger.info(f"Initializing ImageEditor on {self.device} with {self.dtype}")

        try:
            self.pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(
                model,
                torch_dtype=self.dtype,
                safety_checker=None,
            )
            self.pipe.to(self.device)
            self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                self.pipe.scheduler.config
            )

            if self.device == "mps":
                self.pipe.enable_attention_slicing()

            logger.info("Pipeline loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load pipeline: {e}")
            raise e

    def _get_device_and_dtype(self) -> Tuple[str, torch.dtype]:
        if torch.backends.mps.is_available():
            return "mps", torch.float32
        elif torch.cuda.is_available():
            return "cuda", torch.float16
        else:
            return "cpu", torch.float32

    def resize_image(self, image: Image.Image, max_pixels: int) -> Image.Image:
        w, h = image.size
        current_pixels = w * h

        if current_pixels <= max_pixels * max_pixels:
            return image

        scale_factor = math.sqrt(max_pixels * max_pixels / current_pixels)
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)

        logger.debug(f"Resizing from {w}x{h} to {new_w}x{new_h}")
        return image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    @torch.inference_mode()
    def edit_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        max_pixels: int,
        steps: int,
        guidance_scale: float = 7.5,
        image_guidance_scale: float = 1.5,
    ) -> bool:
        try:
            image = Image.open(image_path).convert("RGB")
            image = self.resize_image(image, max_pixels)

            generator = torch.manual_seed(42)

            output = self.pipe(
                image=image,
                prompt=prompt,
                generator=generator,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                image_guidance_scale=image_guidance_scale,
            )

            output_image = output.images[0]
            output_image.save(output_path)
            logger.info(f"Saved edited image to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error editing {image_path}: {e}")
            return False


def main():
    args = parse_args()

    editor = ImageEditor(args.model)

    os.makedirs(args.output_dir, exist_ok=True)

    image_paths = glob(os.path.join(args.input_dir, "*"))

    logger.info(
        f"Starting editing for {len(image_paths)} images. Prompt: '{args.prompt}'"
    )
    success_count = 0
    for img_path in tqdm(image_paths, desc="Editing Images"):
        filename = os.path.basename(img_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_edited{ext}"
        output_path = os.path.join(args.output_dir, output_filename)

        if editor.edit_image(
            img_path,
            args.prompt,
            output_path,
            max_pixels=args.max_pixels,
            steps=args.steps,
        ):
            success_count += 1

    logger.info(f"Finished. Success: {success_count}/{len(image_paths)}")
    print(f"Finished. Success: {success_count}/{len(image_paths)}")


def parse_args():
    parser = argparse.ArgumentParser(description="Edit images using GenAI")
    parser.add_argument("--input-dir", type=str, required=True, help="Input directory")
    parser.add_argument(
        "--output-dir", type=str, required=True, help="Output directory"
    )
    parser.add_argument("--prompt", type=str, required=True, help="Editing instruction")
    parser.add_argument("--model", type=str, default="timbrooks/instruct-pix2pix")
    parser.add_argument(
        "--max-pixels",
        type=int,
        default=512,
        help="Max pixels",
    )
    parser.add_argument("--steps", type=int, default=30, help="Inference steps")
    return parser.parse_args()


if __name__ == "__main__":
    main()
