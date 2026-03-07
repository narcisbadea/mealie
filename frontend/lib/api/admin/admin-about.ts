import { BaseAPI } from "../base/base-clients";
import type { AdminAboutInfo, AvailableLLMModels, CheckAppConfig, LLMModel } from "~/lib/api/types/admin";

const prefix = "/api";

const routes = {
  about: `${prefix}/admin/about`,
  aboutStatistics: `${prefix}/admin/about/statistics`,
  check: `${prefix}/admin/about/check`,
  models: `${prefix}/admin/about/models`,
  docker: `${prefix}/admin/about/docker/validate`,
  validationFile: `${prefix}/media/docker/validate.txt`,
};

export class AdminAboutAPI extends BaseAPI {
  async about() {
    return await this.requests.get<AdminAboutInfo>(routes.about);
  }

  async statistics() {
    return await this.requests.get(routes.aboutStatistics);
  }

  async checkApp() {
    return await this.requests.get<CheckAppConfig>(routes.check);
  }

  async getAvailableModels() {
    return await this.requests.get<AvailableLLMModels>(routes.models);
  }

  async setLLMModel(modelId: string) {
    return await this.requests.post<LLMModel>(routes.models, { id: modelId, name: modelId });
  }

  async resetLLMModel() {
    return await this.requests.delete(routes.models);
  }

  async getDockerValidateFileContents() {
    return await this.requests.get<string>(routes.validationFile);
  }
}
