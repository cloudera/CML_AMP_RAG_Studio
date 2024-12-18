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
 * Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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

import { useState } from "react";
import { useGetDocumentSummary } from "src/api/summaryApi.ts";
import { Popover, Tooltip } from "antd";
import Icon, {
  ExclamationCircleOutlined,
  LoadingOutlined,
  MinusCircleOutlined,
  PauseCircleOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import DocumentationIcon from "src/cuix/icons/DocumentationIcon.ts";
import {
  RagDocumentResponseType,
  RagDocumentStatus,
} from "src/api/ragDocumentsApi.ts";
import { cdlAmber600, cdlRed400 } from "src/cuix/variables.ts";

const SummaryPopover = ({
  dataSourceId,
  timestamp,
  docId,
}: {
  dataSourceId: string;
  timestamp: number | null;
  docId: string;
}) => {
  const [visible, setVisible] = useState(false);
  const documentSummary = useGetDocumentSummary({
    data_source_id: dataSourceId,
    doc_id: docId,
    queryEnabled: timestamp != null && visible,
  });

  return (
    <Popover
      title="Generated summary"
      content={<div style={{ width: 400 }}>{documentSummary.data}</div>}
      open={visible && documentSummary.isSuccess}
      onOpenChange={setVisible}
    >
      <Icon
        component={DocumentationIcon}
        style={{ fontSize: 20 }}
        data-testid="documentation-icon"
      />
    </Popover>
  );
};

const SummaryColumn = ({
  file,
  summarizationModel,
  dataSourceId,
}: {
  file: RagDocumentResponseType;
  summarizationModel?: string;
  dataSourceId: string;
}) => {
  if (!summarizationModel) {
    return (
      <Popover
        title={"No summary available"}
        content={"A summarization model must be selected."}
      >
        <MinusCircleOutlined style={{ fontSize: 16 }} />
      </Popover>
    );
  }
  if (
    file.summaryStatus === RagDocumentStatus.ERROR &&
    file.summaryCreationTimestamp !== null
  ) {
    return (
      <Tooltip title={file.summaryError}>
        <ExclamationCircleOutlined style={{ color: cdlRed400 }} />
      </Tooltip>
    );
  }

  if (file.summaryCreationTimestamp == null) {
    if (file.summaryStatus === RagDocumentStatus.IN_PROGRESS) {
      return <LoadingOutlined spin />;
    }

    if (file.summaryStatus === RagDocumentStatus.ERROR) {
      return (
        <Tooltip title={file.summaryError}>
          <WarningOutlined style={{ color: cdlAmber600, marginRight: 8 }} />
          <LoadingOutlined spin />
        </Tooltip>
      );
    }

    return <PauseCircleOutlined />;
  }

  return (
    <SummaryPopover
      dataSourceId={dataSourceId}
      docId={file.documentId}
      timestamp={file.summaryCreationTimestamp}
    />
  );
};

export default SummaryColumn;
