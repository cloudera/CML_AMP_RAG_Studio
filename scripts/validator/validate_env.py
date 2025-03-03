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
import socket


def validate():
    print("Validating environment variables...")
    #  aws
    access_key_id = os.environ.get("AWS_ACCESS_KEY_ID") or None
    secret_key_id = os.environ.get("AWS_SECRET_ACCESS_KEY") or None
    default_region = os.environ.get("AWS_DEFAULT_REGION") or None
    document_bucket = os.environ.get("S3_RAG_DOCUMENT_BUCKET") or None

    # azure
    azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY") or None
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT") or None
    openai_api_version = os.environ.get("OPENAI_API_VERSION") or None

    # caii
    caii_domain = os.environ.get("CAII_DOMAIN") or None

    # 1. if you don't have a caii_domain, you _must_ have an access key, secret key, and default region
    if caii_domain is not None:
        print("Using CAII for LLMs/embeddings; CAII_DOMAIN is set")
        try:
            socket.gethostbyname(caii_domain)
            print(f"CAII domain {caii_domain} can be resolved")
        except socket.error:
            print(f"ERROR: CAII domain {caii_domain} can not be resolved")
            exit(1)
    elif any([access_key_id, secret_key_id, default_region]):
        if all([access_key_id, secret_key_id, default_region]):
            print(
                "Using Bedrock for LLMs/embeddings; AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION are set"
            )

        # 2. if you have a document_bucket, you _must_ have an access key, secret key, and default region
        if document_bucket is not None:
            if access_key_id is None or secret_key_id is None or default_region is None:
                print(
                    "ERROR: Using S3 for document storage; missing required environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
                )
                exit(1)

        if document_bucket is not None:
            print("Using S3 for document storage (S3_RAG_DOCUMENT_BUCKET is set)")
        else:
            print(
                "Using the project filesystem for document storage (S3_RAG_DOCUMENT_BUCKET is not set)"
            )
            # TODO: verify that the bucket prefix is always optional
    elif all([azure_openai_api_key, azure_openai_endpoint, openai_api_version]):
        print(
            "Using Azure for LLMs/embeddings; AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and OPENAI_API_VERSION are set"
        )
    else:
        print("ERROR: Missing required environment variables for modeling serving")
        print(
            "ERROR: If using Bedrock for LLMs/embeddings; missing required environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
        )
        print(
            "ERROR: If using Azure for LLMs/embeddings; missing required environment variables: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, OPENAI_API_VERSION"
        )
        print(
            "ERROR: If using CAII for LLMs/embeddings; missing required environment variables: CAII_DOMAIN"
        )
        exit(1)


validate()
