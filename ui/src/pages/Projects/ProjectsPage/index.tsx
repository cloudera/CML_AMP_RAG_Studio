import { useSuspenseQuery } from "@tanstack/react-query";
import { Card, Flex, Typography } from "antd";
import { getProjectsQueryOptions, Project } from "src/api/projectsApi";
import { format } from "date-fns";
import { useNavigate } from "@tanstack/react-router";

const ProjectCard = ({ project }: { project: Project }) => {
  const navigate = useNavigate();

  const handleOpenProject = () => {
    navigate({ to: `/projects/${project.id.toString()}` }).catch(() => null);
  };

  return (
    <Card
      title={project.name}
      style={{ width: 300 }}
      onClick={handleOpenProject}
      hoverable={true}
    >
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
      style={{
        width: "80%",
        maxWidth: 1000,
        padding: 40,
      }}
      gap={20}
    >
      <Flex gap={24}>
        {projects.data.map((project) => {
          return <ProjectCard project={project} key={project.id} />;
        })}
      </Flex>
    </Flex>
  );
};

export default ProjectsPage;
