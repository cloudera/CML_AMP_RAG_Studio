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
import { Layout, Typography } from "antd";
import { Sessions } from "pages/Projects/ProjectPage/Sessions.tsx";
import { useProjectContext } from "pages/Projects/ProjectContext.tsx";
import { ProjectKnowledgeBases } from "pages/Projects/ProjectPage/ProjectKnowledgeBases.tsx";
import "./index.css";

const ProjectPage = () => {
  const { project } = useProjectContext();

  return (
    <Layout style={{ height: "100%", width: "100%" }}>
      <Layout.Header>
        <Typography.Title level={2}>{project.name}</Typography.Title>
      </Layout.Header>
      <Layout style={{ height: "100%", width: "100%" }}>
        <Layout.Content
          style={{
            height: "20vh",
            overflowY: "auto",
            width: "100%",
            paddingRight: 20,
          }}
        >
          <Sessions />
        </Layout.Content>
        <div className="project-sider">
          <Layout.Sider
            style={{
              width: "30%",
              height: "100vh",
              overflowY: "auto",
              padding: 20,
            }}
          >
            <ProjectKnowledgeBases />
          </Layout.Sider>
        </div>
      </Layout>
      <Layout.Footer>Hello</Layout.Footer>
    </Layout>
  );
};

export default ProjectPage;
