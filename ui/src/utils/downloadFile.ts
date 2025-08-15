/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import messageQueue from "src/utils/messageQueue.ts";

export const downloadFile = async (
  url: string,
  filename: string,
  options?: { pageNumber?: string }
) => {
  const isPdf = filename.toLowerCase().endsWith(".pdf");

  if (isPdf && options?.pageNumber) {
    try {
      const res = await fetch(url, { method: "GET" });
      if (!res.ok) {
        if (res.status === 404) {
          messageQueue.error(`File not found for file: ${filename}`);
        } else {
          messageQueue.error(`Failed to download file (${String(res.status)})`);
        }
        return;
      }
      const arrayBuffer = await res.arrayBuffer();
      const pdfBlob = new Blob([arrayBuffer], { type: "application/pdf" });
      const objectUrl = URL.createObjectURL(pdfBlob);
      window.open(
        `${objectUrl}#page=${options.pageNumber}`,
        "_blank",
        "noopener"
      );
      // Note: do not revoke immediately to avoid breaking the viewer tab
    } catch {
      messageQueue.error("Failed to download file");
    }
    return;
  }

  try {
    const res = await fetch(url, { method: "HEAD" });
    if (res.ok) {
      window.location.href = url;
    } else if (res.status === 404) {
      messageQueue.error(`File not found for file: ${filename}`);
    } else {
      messageQueue.error(`Failed to download file (${String(res.status)})`);
    }
  } catch {
    messageQueue.error("Failed to download file");
  }
};
