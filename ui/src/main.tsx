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

import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { routeTree } from "./routeTree.gen";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import "./index.css";
import { ApiError } from "./api/utils";
import { Flex, Spin, Typography } from "antd";
import { NotFoundComponent } from "src/components/ErrorComponents/NotFoundComponent.tsx";
import { CustomUnhandledError } from "src/components/ErrorComponents/CustomUnhandledError.tsx";
import "@ant-design/v5-patch-for-react-19";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount: number, error: Error) => {
        if (error instanceof ApiError) {
          if (error.status === 502) {
            return false;
          }
          if (error.message.includes("No such file or directory: '/tmp/jwt'")) {
            return false;
          }
          if (failureCount > 4) {
            return false;
          }
          return error.status >= 500;
        }
        return failureCount <= 4;
      },
    },
  },
});

const router = createRouter({
  routeTree,
  context: { queryClient: queryClient },
  defaultErrorComponent: (error) => <CustomUnhandledError error={error} />,
  defaultNotFoundComponent: () => <NotFoundComponent />,
  defaultPendingComponent: () => (
    <Flex
      align="center"
      justify="center"
      style={{ height: "100vh", width: "100%" }}
      vertical
      gap={20}
    >
      <Typography.Text type="secondary">RAG Studio</Typography.Text>
      <Spin spinning />
    </Flex>
  ),
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

ReactDOM.createRoot(document.getElementById("root") as HTMLDivElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      {/*<ReactQueryDevtools initialIsOpen={false} />*/}
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
);
