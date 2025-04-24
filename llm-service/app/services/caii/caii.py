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




pre_time = time.time()
from typing import Callable, List, Sequence
print(f'from typing import Callable, List, Sequence took {time.time() - start_time:.3f} seconds')




pre_time = time.time()
import requests
print(f'import requests took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from fastapi import HTTPException
print(f'from fastapi import HTTPException took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.core.base.embeddings.base import BaseEmbedding
print(f'from llama_index.core.base.embeddings.base import BaseEmbedding took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.core.base.llms.types import ChatMessage
print(f'from llama_index.core.base.llms.types import ChatMessage took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.core.llms import LLM
print(f'from llama_index.core.llms import LLM took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.core.postprocessor.types import BaseNodePostprocessor
print(f'from llama_index.core.postprocessor.types import BaseNodePostprocessor took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.llms.nvidia import NVIDIA
print(f'from llama_index.llms.nvidia import NVIDIA took {time.time() - start_time:.3f} seconds')




pre_time = time.time()
from .CaiiEmbeddingModel import CaiiEmbeddingModel
print(f'from .CaiiEmbeddingModel import CaiiEmbeddingModel took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from .CaiiModel import DeepseekModel
print(f'from .CaiiModel import DeepseekModel took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from .caii_reranking import CaiiRerankingModel
print(f'from .caii_reranking import CaiiRerankingModel took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from .types import Endpoint, ListEndpointEntry, ModelResponse
print(f'from .types import Endpoint, ListEndpointEntry, ModelResponse took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from .utils import build_auth_headers, get_caii_access_token
print(f'from .utils import build_auth_headers, get_caii_access_token took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from ..utils import raise_for_http_error, body_to_json
print(f'from ..utils import raise_for_http_error, body_to_json took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from ..llama_utils import completion_to_prompt, messages_to_prompt
print(f'from ..llama_utils import completion_to_prompt, messages_to_prompt took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
import logging
print(f'import logging took {time.time() - start_time:.3f} seconds')




pre_time = time.time()
from ...config import settings
print(f'from ...config import settings took {time.time() - start_time:.3f} seconds')



DEFAULT_NAMESPACE = "serving-default"



logger = logging.getLogger(__name__)



def describe_endpoint(endpoint_name: str) -> Endpoint:

    domain = settings.caii_domain

    headers = build_auth_headers()

    describe_url = f"https://{domain}/api/v1alpha1/describeEndpoint"

    desc_json = {"name": endpoint_name, "namespace": DEFAULT_NAMESPACE}



    response = requests.post(describe_url, headers=headers, json=desc_json)

    raise_for_http_error(response)

    return Endpoint(**body_to_json(response))





def list_endpoints() -> list[ListEndpointEntry]:

    domain = settings.caii_domain

    try:

        headers = build_auth_headers()

        describe_url = f"https://{domain}/api/v1alpha1/listEndpoints"

        desc_json = {"namespace": DEFAULT_NAMESPACE}



        response = requests.post(describe_url, headers=headers, json=desc_json)

        raise_for_http_error(response)

        endpoints = body_to_json(response)["endpoints"]

        return [ListEndpointEntry(**endpoint) for endpoint in endpoints]

    except requests.exceptions.ConnectionError:

        raise HTTPException(

            status_code=421,

            detail=f"Unable to connect to host {domain}. Please check your CAII Settings.",

        )





def get_reranking_model(model_name: str, top_n: int) -> BaseNodePostprocessor:

    endpoint = describe_endpoint(endpoint_name=model_name)

    token = get_caii_access_token()

    return CaiiRerankingModel(

        model=endpoint.model_name,

        base_url=endpoint.url.removesuffix("/ranking"),

        api_key=token,

        top_n=top_n,

    )





def get_llm(

    endpoint_name: str,

    messages_to_prompt: Callable[[Sequence[ChatMessage]], str],

    completion_to_prompt: Callable[[str], str],

) -> LLM:

    endpoint = describe_endpoint(endpoint_name=endpoint_name)

    api_base = endpoint.url.removesuffix("/chat/completions")



    model = endpoint.model_name

    # todo: test if the NVIDIA impl works with deepseek, too

    if "deepseek" in endpoint_name.lower():

        return DeepseekModel(

            model=model,

            context=128000,

            messages_to_prompt=messages_to_prompt,

            completion_to_prompt=completion_to_prompt,

            api_base=api_base,

            default_headers=(build_auth_headers()),

        )

    return NVIDIA(

        api_key=get_caii_access_token(),

        base_url=api_base,

        model=model

    )





def get_embedding_model(model_name: str) -> BaseEmbedding:

    endpoint_name = model_name

    endpoint = describe_endpoint(endpoint_name=endpoint_name)

    # todo: figure out if the Nvidia library can be made to work for embeddings as well.

    return CaiiEmbeddingModel(endpoint=endpoint)





# task types from the MLServing proto definition

# TASK_UNKNOWN = 0;

# INFERENCE = 1;

# TEXT_GENERATION = 2;

# EMBED = 3;

# TEXT_TO_TEXT_GENERATION = 4;

# CLASSIFICATION = 5;

# FILL_MASK = 6;

# RANK = 7;





def get_caii_llm_models() -> List[ModelResponse]:

    potential_models = get_models_with_task("TEXT_GENERATION")

    results: list[ModelResponse] = []

    for potential in potential_models:

        try:

            model = get_llm(endpoint_name=potential.name, messages_to_prompt=messages_to_prompt, completion_to_prompt=completion_to_prompt)

            if model.metadata:

                results.append(potential)

        except Exception:

            logger.warning(f"Unable to load model metadata for model: {potential.name}")

            pass



    return results



def get_caii_reranking_models() -> List[ModelResponse]:

    return get_models_with_task("RANK")



def get_caii_embedding_models() -> List[ModelResponse]:

    return get_models_with_task("EMBED")





def get_models_with_task(task_type: str) -> List[ModelResponse]:

    endpoints = list_endpoints()

    endpoint_details = list(

        map(lambda endpoint: describe_endpoint(endpoint.name), endpoints)

    )

    llm_endpoints = list(

        filter(

            lambda endpoint: endpoint.task and endpoint.task == task_type,

            endpoint_details,

        )

    )

    models = list(map(build_model_response, llm_endpoints))

    return models





def build_model_response(endpoint: Endpoint) -> ModelResponse:

    return ModelResponse(

        model_id=endpoint.name,

        name=endpoint.name,

        available=endpoint.replica_count > 0,

        replica_count=endpoint.replica_count,

    )
