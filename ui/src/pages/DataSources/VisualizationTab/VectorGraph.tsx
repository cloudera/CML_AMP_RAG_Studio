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

import { Point2d } from "src/api/dataSourceApi.ts";
import { Skeleton } from "antd";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ScatterSeriesType } from "@mui/x-charts";
import { v4 as uuidv4 } from "uuid";
import { cdlOrange500 } from "src/cuix/variables.ts";
import { useMemo } from "react";

interface PointsTypeValue {
  x: number;
  y: number;
  id: string;
}
type PointsType = Record<string, [PointsTypeValue]>;

const sharedSeriesProps: Pick<
  ScatterSeriesType,
  "type" | "valueFormatter" | "highlightScope"
> = {
  type: "scatter",
  valueFormatter: () => null,
  highlightScope: {
    highlight: "series",
    fade: "global",
  },
};

const prepareData = (
  rawData: Point2d[],
  userInput: string,
): ScatterSeriesType[] => {
  const points: PointsType = {};

  rawData.forEach((d: Point2d, index) => {
    if (d[1] in points) {
      points[d[1]].push({ x: d[0][0], y: d[0][1], id: index.toString() });
    } else {
      points[d[1]] = [{ x: d[0][0], y: d[0][1], id: index.toString() }];
    }
  });

  const formatSeries = ([fileName, points]: [
    keyof PointsType,
    PointsTypeValue[],
  ]): ScatterSeriesType => {
    const id = uuidv4();
    const overrideColor =
      fileName === "USER_QUERY" ? { color: cdlOrange500 } : {};
    return {
      label: fileName === "USER_QUERY" ? `Query: ${userInput}` : fileName,
      id,
      data: points,
      markerSize: fileName === "USER_QUERY" ? 9 : 3,
      ...overrideColor,
      ...sharedSeriesProps,
    };
  };

  return Object.entries(points).map(formatSeries);
};

const VectorGraph = ({
  rawData,
  userInput,
  loading,
}: {
  rawData: Point2d[];
  userInput: string;
  loading: boolean;
}) => {
  const series = useMemo(
    () => prepareData(rawData, userInput),
    [rawData, userInput],
  );

  if (loading) {
    return <Skeleton style={{ width: 700, height: 400 }} active />;
  }

  return (
    <ScatterChart
      width={700}
      height={400}
      series={series}
      slotProps={{
        legend: {
          hidden: true,
        },
      }}
      disableVoronoi={true}
    />
  );
};

export default VectorGraph;
