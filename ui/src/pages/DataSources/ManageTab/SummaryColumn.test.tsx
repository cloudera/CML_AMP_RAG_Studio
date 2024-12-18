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

import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import SummaryColumn from "./SummaryColumn";
import {
  RagDocumentResponseType,
  RagDocumentStatus,
} from "src/api/ragDocumentsApi";

const mockFile = (
  overrides: Partial<RagDocumentResponseType> = {},
): RagDocumentResponseType => ({
  id: 1,
  filename: "test.txt",
  dataSourceId: 1,
  documentId: "1",
  s3Path: "path",
  vectorUploadTimestamp: null,
  sizeInBytes: 0,
  extension: ".txt",
  timeCreated: 0,
  timeUpdated: 0,
  createdById: 1,
  updatedById: 1,
  summaryCreationTimestamp: null,
  summaryStatus: null,
  summaryError: null,
  indexingStatus: null,
  indexingError: null,
  ...overrides,
});

afterEach(() => {
  cleanup();
});

describe("SummaryColumn", () => {
  it("displays the hourglass icon when the status is unset", () => {
    const file = mockFile({
      summaryStatus: null,
      summaryCreationTimestamp: null,
    });
    render(
      <SummaryColumn
        file={file}
        summarizationModel="model-name"
        dataSourceId="1234"
      />,
    );
    const icon = screen.getByRole("img", { name: "hourglass" });
    expect(icon).toBeTruthy();
  });

  it("displays error icon with tooltip when indexing status is ERROR and summary creation timestamp is not null", () => {
    const file = mockFile({
      summaryStatus: RagDocumentStatus.ERROR,
      summaryCreationTimestamp: 1,
      summaryError: "Indexing error",
    });
    render(
      <SummaryColumn
        file={file}
        summarizationModel="model-name"
        dataSourceId="1234"
      />,
    );
    const icon = screen.getByRole("img", { name: "exclamation-circle" });
    expect(icon).toBeTruthy();
  });

  it("displays warning and loading icons with tooltip when indexing status is ERROR and summary creation timestamp is null", () => {
    const file = mockFile({
      summaryStatus: RagDocumentStatus.ERROR,
      summaryCreationTimestamp: null,
      summaryError: "Summary error",
    });
    render(
      <SummaryColumn
        file={file}
        summarizationModel="model-name"
        dataSourceId="1234"
      />,
    );
    const warningIcon = screen.getByRole("img", { name: "warning" });
    const loadingIcon = screen.getByRole("img", { name: "hourglass" });
    expect(warningIcon).toBeTruthy();
    expect(loadingIcon).toBeTruthy();
  });

  it("displays loading icon when summary creation timestamp is null and indexing status is not ERROR", () => {
    const file = mockFile({
      summaryStatus: RagDocumentStatus.IN_PROGRESS,
      summaryCreationTimestamp: null,
    });
    render(
      <SummaryColumn
        file={file}
        summarizationModel="model-name"
        dataSourceId="1234"
      />,
    );
    const loadingIcon = screen.getByRole("img", { name: "loading" });
    expect(loadingIcon).toBeTruthy();
  });

  it("displays document icon when summary creation timestamp is not null and status is success", () => {
    vi.mock("src/api/summaryApi.ts", () => ({
      useGetDocumentSummary: vi.fn(() => ({
        data: "summary data",
        isLoading: false,
      })),
    }));

    const file = mockFile({
      summaryStatus: RagDocumentStatus.SUCCESS,
      summaryCreationTimestamp: 1213,
    });
    render(
      <SummaryColumn
        file={file}
        summarizationModel="model-name"
        dataSourceId="1234"
      />,
    );
    const documentIcon = screen.getByTestId("documentation-icon");
    expect(documentIcon).toBeTruthy();
  });

  it("displays not-available icon when the summarization model is unset", () => {
    const file = mockFile({
      summaryStatus: RagDocumentStatus.SUCCESS,
      summaryCreationTimestamp: 1213,
    });
    render(<SummaryColumn file={file} dataSourceId="1234" />);
    const documentIcon = screen.getByRole("img", { name: "minus-circle" });
    expect(documentIcon).toBeTruthy();
  });
});
