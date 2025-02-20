"""
Reconciler script to process io request pairs.
"""

#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
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

import os
import json
import logging
import sys
import time
import threading
from pathlib import Path
import argparse
import asyncio
from typing import Any, Literal

import mlflow
from mlflow.entities import Experiment
from pydantic import BaseModel
from uvicorn.logging import DefaultFormatter

# Configure logging
logger = logging.getLogger(__name__)
formatter = DefaultFormatter("%(levelprefix)s %(message)s")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

logger.addHandler(handler)


class MlflowTable(BaseModel):
    data: dict[str, Any]
    artifact_file: str
    run_id: str


class MlflowRunData(BaseModel):
    experiment_name: str
    run_name: str
    tags: dict[str, Any]
    metrics: dict[str, int]
    params: dict[str, Any]
    table: MlflowTable


def evaluate_json_data(data: MlflowRunData) -> Literal["success", "failed", None]:

    if data["status"] == "success":
        return None

    if data["status"] == "pending":
        experiment: Experiment = mlflow.set_experiment(
            experiment_name=data["experiment_name"]
        )
        with mlflow.start_run(
            experiment_id=experiment.experiment_id, run_name=data["run_name"]
        ):
            mlflow.log_params(data["params"])
            mlflow.log_metrics(data["metrics"])
            mlflow.set_tags(data["tags"])
            mlflow.log_table(data["table"].data, data["table"].artifact_file)
            return "success"

    return "failed"


async def process_io_pair(file_path, processing_function):
    """Callback function to process a io saved in a file."""
    with open(file_path, "r") as f:
        data = json.load(f)
    # Process io pair
    status = await processing_function(data)
    # save the response
    if status is not None:
        data["status"] = status
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    if status == "pending":
        logger.info(
            "MLFlow experiment and run IDs set for i/o pair: %s. Queued for evaluation.",
            file_path,
        )
        return
    if status == "failed":
        logger.error("Failed to process i/o pair: %s. Will retry.", file_path)
        return


def background_worker(directory, processing_function):
    """Background thread function to process files."""
    if not isinstance(directory, Path):
        directory = Path(directory)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        files_to_process = [
            file_path
            for file_path in directory.iterdir()
            if file_path.is_file() and file_path.suffix == ".json"
        ]
        for file_path in files_to_process:
            try:
                loop.run_until_complete(
                    process_io_pair(
                        file_path=file_path, processing_function=processing_function
                    )
                )
            except Exception as e:
                logger.error("Error processing file %s: %s", file_path, e)
        time.sleep(15)


# Start background worker thread
def start_background_worker(directory, processing_function):
    """Start the background worker thread."""
    if not isinstance(directory, Path):
        directory = Path(directory)
    worker_thread = threading.Thread(
        target=background_worker, args=(directory, processing_function), daemon=True
    )
    worker_thread.start()


if __name__ == "__main__":
    # Directory to save JSON files
    # Argument parsing to get the data directory
    parser = argparse.ArgumentParser(
        description="Reconciler script to process io request pairs."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join("data", "responses"),
        help="Directory to save JSON files",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(exist_ok=True)
    start_background_worker(data_dir, evaluate_json_data)
    try:
        while True:
            logger.info("Reconciler looking for i/o pairs in %s...", data_dir)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
