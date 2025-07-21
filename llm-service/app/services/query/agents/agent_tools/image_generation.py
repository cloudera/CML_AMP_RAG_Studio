#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
#
import abc
import base64
import json
import os
from enum import Enum
from os import PathLike
from typing import Optional

import boto3
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.tools.openai import (
    OpenAIImageGenerationToolSpec as LlamaIndexOpenAIImageGenerationToolSpec,
)
from llama_index.tools.openai.image_generation.base import DEFAULT_SIZE

from app.config import settings


class ImageGeneratorToolSpec(abc.ABC, BaseToolSpec):
    """Base class for image generation tool specs."""

    spec_functions = ["image_generation"]

    def __init__(self, **kwargs) -> None:
        """Initialize with parameters."""
        pass

    @staticmethod
    def get_cache_dir() -> str:
        """Return the cache directory."""
        return os.path.join(settings.rag_databases_dir, "..", "cache")

    @abc.abstractmethod
    def image_generation(self, **kwargs):
        """Generate an image based on the provided parameters."""
        raise NotImplementedError("Subclasses must implement this method.")


class OpenAIImageGenerationToolSpec(
    LlamaIndexOpenAIImageGenerationToolSpec, ImageGeneratorToolSpec
):
    """OpenAI Image Generation tool spec."""

    def __init__(self, api_key: str = None) -> None:
        """Initialize with parameters."""
        super().__init__(
            api_key=api_key, cache_dir=ImageGeneratorToolSpec.get_cache_dir()
        )

    def image_generation(
        self,
        text: str,
        model: Optional[str] = "dall-e-3",
        quality: Optional[str] = "standard",
        num_images: Optional[int] = 1,
        size: Optional[str] = DEFAULT_SIZE,
        style: Optional[str] = "vivid",
        timeout: Optional[int] = None,
        download: Optional[bool] = None,  # For backward compatibility
    ) -> str:
        return super().image_generation(
            text=text,
            model=model,
            quality=quality,
            num_images=num_images,
            size=size,
            style=style,
            timeout=timeout,
            download=False,  # Default to not downloading
        )


class BedrockImageGenerationToolSpec(ImageGeneratorToolSpec):
    """Bedrock Image Generation tool spec."""

    spec_functions = ["image_generation"]

    def __init__(self, **kwargs) -> None:
        """Initialize with parameters."""
        super().__init__(**kwargs)
        self.client = boto3.client("bedrock-runtime")

    def image_generation(
        self,
        text: str,
        image_name: str,
        model: Optional[str] = "amazon.titan-image-generator-v2:0",
        quality: Optional[str] = "standard",
        num_images: Optional[int] = 1,
        size: Optional[str] = "512x512",
        cfg_scale: Optional[float] = 8.0,
        **kwargs,
    ) -> str:
        """Generate an image using Bedrock."""
        native_request = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": text},
            "imageGenerationConfig": {
                "numberOfImages": num_images,
                "quality": quality,
                "cfgScale": cfg_scale,
                "height": int(size.split("x")[1]),
                "width": int(size.split("x")[0]),
            },
        }

        request = json.dumps(native_request)

        response = self.client.invoke_model(modelId=model, body=request)
        model_response = json.loads(response["body"].read())
        base64_image_data = model_response["images"][0]
        image_data = base64.b64decode(base64_image_data)

        # Save the image to the cache directory
        image_path = os.path.join(self.get_cache_dir(), f"{image_name}.png")
        # Create cache directory if it doesn't exist
        os.makedirs(self.get_cache_dir(), exist_ok=True)
        with open(image_path, "wb") as file:
            file.write(image_data)
        return image_path
