/*******************************************************************************
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2024
 * All rights reserved.
 *
 * Applicable Open Source License: Apache 2.0
 *
 * NOTE: Cloudera open source products are modular software products
 * made up of hundreds of individual components, each of which was
 * individually copyrighted.  Each Cloudera open source product is a
 * collective work under U.S. Copyright Law. Your license to use the
 * collective work is as provided in your written agreement with
 * Cloudera.  Used apart from the collective work, this file is
 * licensed for your use pursuant to the open source license
 * identified above.
 *
 * This code is provided to you pursuant a written agreement with
 * (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
 * this code. If you do not have a written agreement with Cloudera nor
 * with an authorized and properly licensed third party, you do not
 * have any rights to access nor to use this code.
 *
 * Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
 * contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
 * KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
 * WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
 * IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
 * FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
 * AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
 * ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
 * OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
 * CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
 * RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
 * BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
 * DATA.
 ******************************************************************************/

import { Flex, Typography } from "antd";
import { SourceCard } from "pages/RagChatTab/ChatOutput/Sources/SourceCard.tsx";
import { ChatMessageType } from "src/api/chatApi.ts";
import { WarningTwoTone } from "@ant-design/icons";
import { cdlOrange050, cdlOrange500 } from "src/cuix/variables.ts";
import { useGetLlmModels } from "src/api/modelsApi.ts";

const SourceNodes = ({ data }: { data: ChatMessageType }) => {
  const { data: inferenceModels } = useGetLlmModels();

  const nodes = data.source_nodes.map((node) => (
    <SourceCard key={node.node_id} source={node} />
  ));

  const modelName = () => {
    if (!data.inference_model) {
      return "the model";
    }
    const model = inferenceModels
      ?.filter((model) => model.model_id === data.inference_model)
      .pop();
    return model?.name ?? "the model";
  };

  if (nodes.length === 0) {
    return (
      <Flex
        style={{ gap: 8, padding: "6px 12px", backgroundColor: cdlOrange050 }}
      >
        <WarningTwoTone twoToneColor={cdlOrange500} />
        <Typography.Text>
          This answer is provided directly by{" "}
          <Typography.Text style={{ fontWeight: "bold" }}>
            {modelName()}
          </Typography.Text>{" "}
          and does not reference the Knowledge Base.
        </Typography.Text>
      </Flex>
    );
  }
  return (
    <Flex wrap="wrap" style={{ gap: 8 }}>
      {nodes}
    </Flex>
  );
};

export default SourceNodes;
