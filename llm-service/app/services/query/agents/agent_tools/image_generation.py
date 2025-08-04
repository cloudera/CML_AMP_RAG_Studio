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
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import boto3
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.tools.openai import (
    OpenAIImageGenerationToolSpec as LlamaIndexOpenAIImageGenerationToolSpec,
)
from llama_index.tools.openai.image_generation.base import DEFAULT_SIZE

from app.config import settings
from app.services.query.agents.agent_tools.stable_diffusion_types import (
    StableDiffusionRequest,
    GenerationMode,
    AspectRatio,
)
from app.services.query.agents.agent_tools.titan_image_types import (
    TitanImageRequest,
    TextToImageParams,
    TitanImageGenerationConfig,
    ValidTitanImageSizes,
)


# Define image generation tool IDs for different providers
class ImageGenerationTools(str, Enum):
    """Enum for image generation tool IDs."""

    OPENAI_IMAGE_GENERATION = "openai-image-generation"
    BEDROCK_STABLE_DIFFUSION = "bedrock-stable-diffusion"
    BEDROCK_TITAN_IMAGE = "bedrock-titan-image"


# Tool metadata for UI display
IMAGE_GENERATION_TOOL_METADATA: Dict[str, Dict[str, Any]] = {
    ImageGenerationTools.OPENAI_IMAGE_GENERATION: {
        "display_name": "OpenAI Image Generation",
        "description": "Generate images using OpenAI's DALL-E model",
    },
    ImageGenerationTools.BEDROCK_STABLE_DIFFUSION: {
        "display_name": "Stable Diffusion (Bedrock)",
        "description": "Generate images using Stable Diffusion models on AWS Bedrock",
    },
    ImageGenerationTools.BEDROCK_TITAN_IMAGE: {
        "display_name": "Titan Image Generator (Bedrock)",
        "description": "Generate images using Amazon's Titan Image Generator on AWS Bedrock",
    },
}


class ImageGeneratorToolSpec(abc.ABC, BaseToolSpec):
    """Base class for image generation tool specs."""

    spec_functions = ["image_generation"]

    @staticmethod
    def get_cache_dir() -> str:
        """Return the cache directory."""
        return os.path.abspath(os.path.join(settings.rag_databases_dir, "..", "cache"))

    @abc.abstractmethod
    def image_generation(self, *args: Any, **kwargs: Any) -> str:
        """Generate an image based on the provided parameters."""
        raise NotImplementedError("Subclasses must implement this method.")


class OpenAIImageGenerationToolSpec(
    LlamaIndexOpenAIImageGenerationToolSpec,
    ImageGeneratorToolSpec,
):
    """OpenAI Image Generation tool spec."""

    def __init__(self, api_key: str = None) -> None:
        """Initialize with parameters."""
        super().__init__(
            api_key=api_key,
            cache_dir=ImageGeneratorToolSpec.get_cache_dir(),
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
        download: bool = True,  # For suppressing signature error
    ) -> str:
        """
        This tool accepts a natural language string and will use OpenAI's DALL-E model to generate an image.

        Args:
            text: The text to generate an image from.

            model: The model to use for image generation. Defaults to `dall-e-3`.
                Must be one of `dall-e-2` or `dall-e-3`.

            num_images: The number of images to generate. Defaults to 1.
                Must be between 1 and 10. For `dall-e-3`, only `n=1` is supported.

            quality: The quality of the image that will be generated. Defaults to `standard`.
                Must be one of `standard` or `hd`. `hd` creates images with finer
                details and greater consistency across the image. This param is only supported
                for `dall-e-3`.

            size: The size of the generated images. Defaults to `1024x1024`.
                Must be one of `256x256`, `512x512`, or `1024x1024` for `dall-e-2`.
                Must be one of `1024x1024`, `1792x1024`, or `1024x1792` for `dall-e-3` models.

            style: The style of the generated images. Defaults to `vivid`.
                Must be one of `vivid` or `natural`.
                Vivid causes the model to lean towards generating hyper-real and dramatic images.
                Natural causes the model to produce more natural, less hyper-real looking images.
                This param is only supported for `dall-e-3`.

            timeout: Override the client-level default timeout for this request, in seconds. Defaults to `None`.
        """
        image_path = super().image_generation(
            text=text,
            model=model,
            quality=quality,
            num_images=num_images,
            size=size,
            style=style,
            timeout=timeout,
            download=True,
        )
        image_name = Path(image_path[0]).name
        return f"/cache/{image_name}"


class BedrockStableDiffusionToolSpec(ImageGeneratorToolSpec):
    """Bedrock Stable Diffusion Image Generation tool spec."""

    def __init__(
        self,
        model: str = "stability.sd3-5-large-v1:0",
        **kwargs: Any,
    ) -> None:
        """Initialize with parameters."""
        super().__init__(**kwargs)
        self.client = boto3.client("bedrock-runtime")
        self.model = model

    def image_generation(
        self,
        text: str,
        image_name: str,
        seed: int = 42,
        negative_text: str = "",
        aspect_ratio: Optional[AspectRatio] = AspectRatio.RATIO_5_4,
    ) -> str:
        """
        Generate an image using Stable Diffusion models on Bedrock.

        Parameters:
            text (str): The prompt for image generation.
            image_name (str): The name to save the generated image as.
            quality (Literal["standard", "premium"], optional): Image quality.
            num_images (int, optional): Number of images to generate.
            seed (int, optional): Random seed for generation.
            negative_text (str, optional): Negative prompt for image generation.
            aspect_ratio (AspectRatio, optional): Aspect ratio for the generated image.

        Returns:
            str: Path to the generated image in the cache directory.
        """
        # Create Stable Diffusion Pydantic model instance
        sd_request = StableDiffusionRequest(
            prompt=text,
            negative_prompt=negative_text,
            mode=GenerationMode.TEXT_TO_IMAGE,
            seed=seed,
            aspect_ratio=aspect_ratio,
        )

        # Convert to JSON for API request
        request = sd_request.model_dump_json()

        # Call the Bedrock API
        return _get_image_from_bedrock(
            boto3_bedrock_client=self.client,
            model=self.model,
            request=request,
            image_name=image_name,
            cache_dir=self.get_cache_dir(),
        )


class BedrockTitanImageToolSpec(ImageGeneratorToolSpec):
    """Bedrock Titan Image Generation tool spec."""

    def __init__(
        self,
        model: str = "amazon.titan-image-generator-v2:0",
        **kwargs: Any,
    ) -> None:
        """Initialize with parameters."""
        super().__init__(**kwargs)
        self.client = boto3.client("bedrock-runtime")
        self.model = model

    def image_generation(
        self,
        text: str,
        image_name: str,
        quality: Literal["standard", "premium"] = "standard",
        num_images: int = 1,
        seed: int = 42,
        negative_text: str = "",
        cfg_scale: float = 8.0,
        size: ValidTitanImageSizes = ValidTitanImageSizes.SMALL,
    ) -> str:
        """
        Generate an image using Amazon Titan Image Generator on Bedrock.

        Parameters:
            text (str): The prompt for image generation.
            image_name (str): The name to save the generated image as.
            quality (Literal["standard", "premium"], optional): Image quality.
            num_images (int, optional): Number of images to generate.
            seed (int, optional): Random seed for generation.
            negative_text (str, optional): Negative prompt for image generation.
            cfg_scale (float, optional): Configuration scale for generation.
            size (ValidTitanImageSizes, optional): Image size for generation.

        Returns:
            str: Path to the generated image in the cache directory.
        """
        # Create Titan Pydantic model instances
        text_to_image_params = TextToImageParams(text=text, negativeText=negative_text)
        image_generation_config = TitanImageGenerationConfig(
            numberOfImages=num_images,
            quality=quality,
            cfgScale=cfg_scale,
            width=size[0],
            height=size[1],
            seed=seed,
        )

        titan_request = TitanImageRequest(
            taskType="TEXT_IMAGE",
            textToImageParams=text_to_image_params,
            imageGenerationConfig=image_generation_config,
        )

        # Convert to JSON for API request
        request = titan_request.model_dump_json()

        # Call the Bedrock API
        return _get_image_from_bedrock(
            boto3_bedrock_client=self.client,
            model=self.model,
            request=request,
            image_name=image_name,
            cache_dir=self.get_cache_dir(),
        )


def _get_image_from_bedrock(
    boto3_bedrock_client: Any,
    model: str,
    request: str,
    image_name: str,
    cache_dir: str,
) -> str:
    """
    Helper function to get an image from Bedrock and save it to the cache directory.

    Parameters:
        boto3_bedrock_client: The Bedrock client.
        model: The model ID to use for image generation.
        request: The request payload for the model.
        image_name (str): The name to save the generated image as.
        cache_dir (str): The directory to save the image in.

    Returns:
        str: Path to the generated image in the cache directory.
    """
    response = boto3_bedrock_client.invoke_model(modelId=model, body=request)
    model_response = json.loads(response["body"].read())
    base64_image_data = model_response["images"][0]
    image_data = base64.b64decode(base64_image_data)

    # Save the image to the cache directory
    image_path = os.path.join(cache_dir, f"{image_name}.png")
    os.makedirs(cache_dir, exist_ok=True)
    if os.path.exists(image_path):
        # use a different name for the image
        i = 1
        # increment the number until the image does not exist
        while os.path.exists(image_path):
            image_name = f"{image_name}_{i}"
            image_path = os.path.join(cache_dir, f"{image_name}.png")
            i += 1
    with open(image_path, "wb") as file:
        file.write(image_data)
    return f"/cache/{image_name}.png"
