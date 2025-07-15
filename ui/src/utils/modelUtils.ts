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
import { useMemo } from "react";
import { Model, useGetModelSource } from "src/api/modelsApi.ts";

export const transformModelOptions = (models?: Model[]) => {
  if (!models) {
    return [];
  }
  return models.map((model) => ({
    value: model.model_id,
    label: model.name,
  }));
};

const REGION_PREFIXES = ["us", "eu", "apac"];

const getModelFamily = (modelId: string): string => {
  const parts = modelId.split(".");
  if (REGION_PREFIXES.includes(parts[0])) {
    parts.shift();
  }
  const family = parts[0]?.trim();
  return family || "other";
};

const capitalizeFirst = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export type ModelSelectOptions = (
  | { value: string; label: string }
  | {
      label: string;
      options: {
        value: string;
        label: string;
      }[];
    }
)[];

export const useTransformModelOptions = (
  models?: Model[],
): ModelSelectOptions => {
  const { data: modelSource } = useGetModelSource();

  return useMemo(() => {
    if (!models) {
      return [];
    }

    // For Bedrock, group by model family
    if (modelSource === "Bedrock") {
      const familyGroups: Record<string, Model[]> = {};

      models.forEach((model) => {
        const family = getModelFamily(model.model_id);
        if (!(family in familyGroups)) {
          familyGroups[family] = [];
        }
        familyGroups[family].push(model);
      });

      return Object.entries(familyGroups).map(([family, familyModels]) => ({
        label: capitalizeFirst(family),
        options: familyModels.map((model) => ({
          value: model.model_id,
          label: model.name,
        })),
      }));
    }

    // For all other model providers, return flat options
    return models.map((model) => ({
      value: model.model_id,
      label: model.name,
    }));
  }, [models, modelSource]);
};
