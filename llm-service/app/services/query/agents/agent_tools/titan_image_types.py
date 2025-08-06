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
import enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TextToImageParams(BaseModel):
    """Parameters for text to image generation."""

    text: str = Field(..., description="The text prompt for image generation")
    negativeText: Optional[str] = Field(
        None, description="A text prompt to define what not to include in the image"
    )


class TitanImageGenerationConfig(BaseModel):
    """Configuration parameters for image generation."""

    numberOfImages: int = Field(
        1, ge=1, le=5, description="Number of images to generate (1-5)"
    )
    quality: Literal["standard", "premium"] = Field(
        "standard", description="Quality of the generated image"
    )
    cfgScale: float = Field(
        8.0, ge=1.1, le=10.0, description="Configuration scale parameter (1.1-10.0)"
    )
    width: int = Field(512, description="Width of the generated image in pixels")
    height: int = Field(512, description="Height of the generated image in pixels")
    seed: Optional[int] = Field(
        42,
        ge=0,
        le=2147483646,
        description="Seed for reproducible results (0-2,147,483,646)",
    )


class TitanImageRequest(BaseModel):
    """Titan Image Generation Request model matching the Amazon Bedrock Titan model requirements."""

    taskType: Literal["TEXT_IMAGE"] = Field(
        default="TEXT_IMAGE", description="Type of task for image generation"
    )
    textToImageParams: TextToImageParams = Field(
        ..., description="Text to image parameters"
    )
    imageGenerationConfig: TitanImageGenerationConfig = Field(
        ..., description="Image generation configuration"
    )


class ValidTitanImageSizes(tuple[int, int], enum.Enum):
    LARGE = (1024, 1024)
    MEDIUM = (768, 768)
    SMALL = (512, 512)
