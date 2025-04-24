import time
start_time = time.time()
# ##############################################################################
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
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
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
# ##############################################################################

import subprocess


def get_current_git_hash() -> str:
    """Retrieve the current git hash of the deployed AMP."""
    try:
        current_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )
        return current_hash
    except subprocess.CalledProcessError:
        raise ValueError("Failed to retrieve current git hash.")


def get_latest_git_hash(current_branch: str) -> str:
    """Retrieve the latest git hash from the remote repository for the current branch."""
    try:
        # Fetch the latest updates from the remote
        subprocess.check_call(["git", "fetch", "origin", current_branch])

        # Get the latest hash for the current branch
        latest_hash = (
            subprocess.check_output(["git", "rev-parse", f"origin/{current_branch}"])
            .strip()
            .decode("utf-8")
        )

        return latest_hash
    except subprocess.CalledProcessError:
        raise ValueError(
            f"Failed to retrieve latest git hash from remote for the branch: {current_branch}."
        )


def check_if_ahead_or_behind(current_hash: str, current_branch: str) -> tuple[int, int]:
    """Check if the current commit is ahead or behind the remote branch."""
    try:
        # Get the number of commits ahead or behind
        ahead_behind = (
            subprocess.check_output(
                [
                    "git",
                    "rev-list",
                    "--left-right",
                    "--count",
                    f"{current_hash}...origin/{current_branch}",
                ]
            )
            .strip()
            .decode("utf-8")
        )

        ahead, behind = map(int, ahead_behind.split())

        return ahead, behind
    except subprocess.CalledProcessError:
        raise ValueError(
            f"Failed to determine if the branch {current_branch} is ahead or behind."
        )


def does_amp_need_updating() -> bool:
    """Check if the AMP is up-to-date. Returns True if the AMP needs updating."""

    # Retrieve the current branch only once
    current_branch = (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .strip()
        .decode("utf-8")
    )

    # Retrieve the current and latest git hashes
    current_hash = get_current_git_hash()
    latest_hash = get_latest_git_hash(current_branch)
    if current_hash and latest_hash:
        if current_hash != latest_hash:
            _, behind = check_if_ahead_or_behind(current_hash, current_branch)
            if behind > 0:
                return True

    return False

print('services/amp_update.py took {time.time() - start_time} seconds to import')
