import { useSuspenseQuery } from "@tanstack/react-query";
import { Card, Flex, Typography } from "antd";
import { getProjectsQueryOptions, Project } from "src/api/projectsApi";
import { format } from "date-fns";

const ProjectCard = ({ project }: { project: Project }) => {
  return (
    <Card title={project.name} style={{ width: 300 }}>
      <Flex vertical>
        <Typography.Text>Creator: {project.createdById}</Typography.Text>
        <Typography.Title level={5}> Created on:</Typography.Title>
        <Typography.Text>
          {format(project.timeCreated * 1000, "MMM dd yyyy, pp")}
        </Typography.Text>
      </Flex>
    </Card>
  );
};

const ProjectsPage = () => {
  const projects = useSuspenseQuery(getProjectsQueryOptions);
  return (
    <Flex
      vertical
      align="end"
      style={{ width: "80%", maxWidth: 1000, marginTop: 40 }}
      gap={20}
    >
      <Flex gap={24}>
        {projects.data.map((project) => {
          return <ProjectCard project={project} />;
        })}
      </Flex>
    </Flex>
  );
};

export default ProjectsPage;
