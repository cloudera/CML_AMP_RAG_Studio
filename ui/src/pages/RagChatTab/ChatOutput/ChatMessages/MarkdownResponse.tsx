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

import { ChatMessageType, SourceNode } from "src/api/chatApi.ts";
import Markdown from "react-markdown";
import Remark from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { ComponentProps, ReactElement } from "react";
import { SourceCard } from "pages/RagChatTab/ChatOutput/Sources/SourceCard.tsx";

export const MarkdownResponse = ({ data }: { data: ChatMessageType }) => {
  return (
    <Markdown
      // skipHtml={true}
      remarkPlugins={[Remark]}
      rehypePlugins={[rehypeRaw]}
      className="styled-markdown"
      children={data.rag_message.assistant.trimStart()}
      components={{
        img: (
          props: ComponentProps<"img">
        ): ReactElement<SourceNode> | undefined => {
          // check if the image src starts with `sandbox:` and replace it with ``
          if (props.src?.startsWith("sandbox:")) {
            props.src = props.src.replace("sandbox:", "");
          }
          return <img {...props} alt={props.alt} style={{ width: "100%" }} />;
        },
        a: (
          props: ComponentProps<"a">
        ): ReactElement<SourceNode> | undefined => {
          const { href, className, children, ...other } = props;
          if (className === "rag_citation") {
            if (data.source_nodes.length === 0) {
              return <span>{props.children}</span>;
            }
            const { source_nodes } = data;
            const sourceNodeIndex = source_nodes.findIndex(
              (source_node) => source_node.node_id === href
            );
            if (sourceNodeIndex >= 0) {
              return (
                <span>
                  {props.children}
                  <SourceCard
                    source={source_nodes[sourceNodeIndex]}
                    index={sourceNodeIndex + 1}
                  />
                </span>
              );
            }
            if (!href?.startsWith("http")) {
              return undefined;
            }
          }
          return (
            <a
              href={href}
              className={className}
              {...other}
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          );
        },
      }}
    />
  );
};
