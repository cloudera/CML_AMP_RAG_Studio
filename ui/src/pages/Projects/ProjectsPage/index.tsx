import { useSuspenseQuery } from "@tanstack/react-query";
import { Card } from "antd";
import { getProjectsQueryOptions, Project } from "src/api/projectsApi";

const ProjectCard = ({ project }: { project: Project }) => {
  return (
    <Card title={project.name}>
      <p>{project.createdById}</p>
      <p>
        {new Date(project.timeCreated * 1000).toLocaleDateString("en-US", {
          month: "long",
          day: "numeric",
          year: "numeric",
          hour: "numeric",
          minute: "numeric",
          second: "numeric",
          timeZone: "UTC",
        })}
      </p>
    </Card>
  );
};

const ProjectsPage = () => {
  const projects = useSuspenseQuery(getProjectsQueryOptions);
  return (
    <div>
      {projects.data.map((project) => {
        return <ProjectCard project={project} />;
      })}
    </div>
  );
};

export default ProjectsPage;
