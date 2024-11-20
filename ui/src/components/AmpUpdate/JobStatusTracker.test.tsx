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

import { cleanup, render, screen } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import JobStatusTracker from "./JobStatusTracker";
import { JobStatus } from "src/api/ampUpdateApi.ts";

afterEach(() => {
  cleanup();
});

describe("JobStatusTracker", () => {
  it("displays Scheduling status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.SCHEDULING} />);
    expect(screen.getByText("Scheduling")).toBeTruthy();
  });

  it("displays Starting status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.STARTING} />);
    expect(screen.getByText("Update Starting")).toBeTruthy();
  });

  it("displays Running status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.RUNNING} />);
    expect(screen.getByText("Update Running")).toBeTruthy();
  });

  it("displays Stopping status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.STOPPING} />);
    expect(screen.getByText("Stopping")).toBeTruthy();
  });

  it("displays Stopped status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.STOPPED} />);
    expect(screen.getByText("Stopped")).toBeTruthy();
  });

  it("displays Unknown status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.UNKNOWN} />);
    expect(screen.getByText("Unknown")).toBeTruthy();
  });

  it("displays Succeeded status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.SUCCEEDED} />);
    expect(screen.getByText("Succeeded")).toBeTruthy();
  });

  it("displays Failed status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.FAILED} />);
    expect(screen.getByText("Failed")).toBeTruthy();
  });

  it("displays Timed out status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.TIMEDOUT} />);
    expect(screen.getByText("Timed out")).toBeTruthy();
  });

  it("displays Restarting status correctly", () => {
    render(<JobStatusTracker jobStatus={JobStatus.RESTARTING} />);
    expect(screen.getByText("Restarting")).toBeTruthy();
  });

  it("displays Unknown status when jobStatus is undefined", () => {
    render(<JobStatusTracker jobStatus={undefined} />);
    expect(screen.getByText("Unknown")).toBeTruthy();
  });
});
