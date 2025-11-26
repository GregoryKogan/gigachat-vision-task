from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoTokenizer,
    AutoProcessor,
)
from qwen_vl_utils import process_vision_info
import torch


model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct", torch_dtype="auto", device_map="auto"
)

max_pixels = 256 * 28 * 28
processor = AutoProcessor.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct", max_pixels=max_pixels
)

image_paths = [
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
    "data/images/06e338748b5328fd968f5d7eb280a2b40ecd2a46.jpg",
]

for image_path in image_paths:
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image_path,
                },
                {"type": "text", "text": "Describe this image."},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )

    device = next(model.parameters()).device
    inputs = inputs.to(device)

    generated_ids = model.generate(**inputs, max_new_tokens=128)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    print(output_text)
