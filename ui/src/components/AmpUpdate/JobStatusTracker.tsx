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

import { JobStatus } from "src/api/ampUpdateApi.ts";
import { Flex, Progress, Typography } from "antd";
import {
  cdlAmber400,
  cdlBlue600,
  cdlGray200,
  cdlGreen600,
  cdlRed600,
} from "src/cuix/variables.ts";

const jobStatusDisplayValue = (jobStatus?: JobStatus): string => {
  const statusMap: Record<JobStatus, string> = {
    [JobStatus.SCHEDULING]: "Scheduling",
    [JobStatus.STARTING]: "Starting",
    [JobStatus.RUNNING]: "Running",
    [JobStatus.STOPPING]: "Stopping",
    [JobStatus.STOPPED]: "Stopped",
    [JobStatus.UNKNOWN]: "Unknown",
    [JobStatus.SUCCEEDED]: "Succeeded",
    [JobStatus.FAILED]: "Failed",
    [JobStatus.TIMEDOUT]: "Timed out",
    [JobStatus.RESTARTING]: "Restarting",
  };

  return jobStatus && statusMap[jobStatus] ? statusMap[jobStatus] : "Unknown";
};

function decideProgressStatus(jobStatus?: JobStatus): [number, string] {
  let percent: number;
  let color = cdlBlue600;

  switch (jobStatus) {
    case JobStatus.SCHEDULING:
      percent = 20;
      break;
    case JobStatus.STARTING:
      percent = 40;
      break;
    case JobStatus.RUNNING:
      percent = 60;
      break;
    case JobStatus.RESTARTING:
      percent = 80;
      break;
    case JobStatus.SUCCEEDED:
      percent = 100;
      color = cdlGreen600;
      break;
    case JobStatus.STOPPING:
    case JobStatus.STOPPED:
    case JobStatus.UNKNOWN:
      percent = 100;
      color = cdlAmber400;
      break;
    case JobStatus.FAILED:
    case JobStatus.TIMEDOUT:
      percent = 100;
      color = cdlRed600;
      break;
    default:
      percent = 0;
      break;
  }
  return [percent, color];
}

const JobStatusTracker = ({ jobStatus }: { jobStatus?: JobStatus }) => {
  const [percent, color] = decideProgressStatus(jobStatus);

  return (
    <Progress
      type="circle"
      percent={percent}
      steps={5}
      trailColor={cdlGray200}
      strokeColor={color}
      strokeWidth={10}
      format={() => (
        <Flex align="center" justify="center">
          <Typography.Text style={{ fontSize: 12, textWrap: "wrap" }}>
            {jobStatusDisplayValue(jobStatus)}
          </Typography.Text>
        </Flex>
      )}
    />
  );
};

export default JobStatusTracker;
