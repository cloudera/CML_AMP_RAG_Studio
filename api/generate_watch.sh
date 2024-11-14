#!/bin/bash

set -eo pipefail

fswatch -o ./defs | xargs -n1 ./generate.sh