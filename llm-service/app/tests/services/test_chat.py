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

import lipsum
from hypothesis import example, given
from hypothesis import strategies as st

from app.services.chat import process_response


@st.composite
def suggested_questions_responses(
    draw: st.DrawFn,
    min_questions: int = 0,
    max_questions: int = 10,
    min_length: int = 0,
    max_length: int = 20,
    generate_bold: bool = True,
    generate_empty: bool = True,
    response_can_be_empty: bool = True,
) -> str:
    """Generate mocked suggested questions as if returned from an LLM."""
    if response_can_be_empty and draw(st.booleans()):
        return "Empty Response"

    suggested_questions: list[str] = []
    num_questions: int = draw(st.integers(min_questions, max_questions))
    for _ in range(num_questions):
        if generate_empty and draw(st.booleans()):
            suggested_questions.append("")
            continue

        bullet: str = draw(st.sampled_from(["*", "-"]))

        question_length: int = draw(st.integers(min_length, max_length))
        question: str = lipsum.generate_words(question_length).replace(" - ", " ")

        if generate_bold and draw(st.booleans()):
            question = f"*{question}*"

        suggested_questions.append(f"{bullet} {question}")

    return "\n".join(suggested_questions)


class TestProcessResponse:
    @given(response=suggested_questions_responses())
    @example(response="Empty Response")
    def test_process_response(self, response: str) -> None:
        """Verify process_response() cleans and filters an LLM's suggested questions."""
        processed_response: list[str] = process_response(response)
        assert len(processed_response) <= 5

        for suggested_question in processed_response:
            assert not suggested_question.startswith("*")
            assert not suggested_question.startswith("-")

            assert not suggested_question.endswith("*")

            assert len(suggested_question.split()) <= 60

            assert suggested_question != "Empty Response"
            assert suggested_question != ""

print(f'tests/services/test_chat.py took {time.time() - start_time:.3f} seconds to import')
