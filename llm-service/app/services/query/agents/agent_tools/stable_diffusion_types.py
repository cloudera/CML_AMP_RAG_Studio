#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
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
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class GenerationMode(str, Enum):
    """Generation mode for Stable Diffusion models."""

    TEXT_TO_IMAGE = "text-to-image"
    IMAGE_TO_IMAGE = "image-to-image"


class AspectRatio(str, Enum):
    """Available aspect ratios for generated images."""

    RATIO_16_9 = "16:9"
    RATIO_1_1 = "1:1"
    RATIO_21_9 = "21:9"
    RATIO_2_3 = "2:3"
    RATIO_3_2 = "3:2"
    RATIO_4_5 = "4:5"
    RATIO_5_4 = "5:4"
    RATIO_9_16 = "9:16"
    RATIO_9_21 = "9:21"


class OutputFormat(str, Enum):
    """Available output formats for generated images."""

    JPEG = "jpeg"
    PNG = "png"


class StableDiffusionRequest(BaseModel):
    """
    Stable Diffusion Request model for Amazon Bedrock.

    This model includes all parameters needed for both text-to-image and image-to-image generation.
    """

    # Required fields
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="What you wish to see in the output image. A strong, descriptive prompt that clearly defines elements, colors, and subjects will lead to better results.",
    )

    # Optional fields with defaults
    mode: GenerationMode = Field(
        default=GenerationMode.TEXT_TO_IMAGE,
        description="Controls whether this is a text-to-image or image-to-image generation.",
    )

    seed: int = Field(
        default=0,
        ge=0,
        le=4294967294,
        description="A specific value that is used to guide the 'randomness' of the generation. (Use 0 for a random seed.)",
    )

    output_format: OutputFormat = Field(
        default=OutputFormat.PNG,
        description="Dictates the content-type of the generated image.",
    )

    negative_prompt: str = Field(
        default="",
        max_length=10000,
        description="Keywords of what you do not wish to see in the output image.",
    )

    aspect_ratio: Optional[AspectRatio] = Field(
        default=AspectRatio.RATIO_1_1,
        description="Controls the aspect ratio of the generated image. Only valid for text-to-image requests.",
    )

    @field_validator("*")
    def validate_mode_specific_fields(cls, v, info):
        """Validate that the appropriate fields are provided based on the generation mode."""
        field_name = info.field_name
        mode = info.data.get("mode")

        # Skip validation if mode is not set yet
        if not mode:
            return v

        if mode == GenerationMode.TEXT_TO_IMAGE:
            # For text-to-image, image and strength should not be provided
            if field_name in ["image", "strength"] and v is not None:
                raise ValueError(
                    f"{field_name} should not be provided for text-to-image generation"
                )

        return v

    class Config:
        """Configuration for the StableDiffusionRequest model."""

        use_enum_values = True  # Use the string values of enums
