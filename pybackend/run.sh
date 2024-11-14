#!/bin/bash

set -eo pipefail

export AWS_PROFILE=cu_eng_ml_cai_dev

cd src
pdm run python run.py
