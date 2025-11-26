import argparse
import json
import logging
import os
from glob import glob
from typing import Optional

import torch
from qwen_vl_utils import process_vision_info
from tqdm import tqdm
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/generate_captions.log")],
)
logger = logging.getLogger(__name__)


class CaptionGenerator:
    def __init__(self, model: str, max_pixels: int):
        logger.info(f"Loading model: {model}")
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model, torch_dtype="auto", device_map="auto"
        )
        logger.info(f"Loading processor for {model} with max pixels: {max_pixels}")
        self.processor = AutoProcessor.from_pretrained(model, max_pixels=max_pixels)
        logger.info(
            f"Caption generator initialized with model: {model} and max pixels: {max_pixels}"
        )

        self.device = self.model.device
        logger.info(f"Model loaded on device: {self.device}")

    @torch.inference_mode()
    def generate(self, image_path: str, prompt: str) -> Optional[str]:
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_path},
                        {"type": "text", "text": prompt},
                    ],
                },
            ]

            text_prompt = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text_prompt],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(self.device)

            generated_ids = self.model.generate(**inputs, max_new_tokens=128)
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            return output_text[0]
        except Exception as e:
            logger.error(f"Error generating caption for {image_path}: {e}")
            return None


def main() -> None:
    args = parse_args()
    caption_generator = CaptionGenerator(args.model, args.max_pixels)

    image_paths = glob(os.path.join(args.input_dir, "*"))
    logger.info(f"Found {len(image_paths)} images in {args.input_dir}")

    if os.path.dirname(args.output_path):
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)

    with open(args.output_path, "w") as f:
        success_count = 0
        for image_path in tqdm(image_paths, desc="Generating captions"):
            caption = caption_generator.generate(image_path, args.prompt)
            if caption:
                print(
                    json.dumps({"image_path": image_path, "caption": caption}),
                    file=f,
                    flush=True,
                )
                success_count += 1

    logger.info(
        f"Successfully saved {success_count}/{len(image_paths)} captions to {args.output_path}"
    )
    print(
        f"Successfully saved {success_count}/{len(image_paths)} captions to {args.output_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate captions for images")
    parser.add_argument(
        "--input-dir", type=str, required=True, help="Directory with images"
    )
    parser.add_argument(
        "--output-path", type=str, required=True, help="Path to output JSONL file"
    )
    parser.add_argument(
        "--model", type=str, default="Qwen/Qwen2.5-VL-3B-Instruct", help="HF Model name"
    )
    parser.add_argument(
        "--max-pixels", type=int, default=256 * 28 * 28, help="Max pixels"
    )
    parser.add_argument(
        "--prompt", type=str, default="Describe this image.", help="Prompt"
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
