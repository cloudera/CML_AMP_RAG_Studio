import { DataSourceApi, DataSourceFilesApi, SessionApi } from "./api/api";
import { Configuration } from "./api/configuration";

const basePath = "http://localhost:8080/api/v1";

const config = new Configuration({
  basePath: basePath,
});
export const dataSourceApi = new DataSourceApi(config);
export const dataSourceFilesApi = new DataSourceFilesApi(config);
export const sessionApi = new SessionApi(config);
