import { BaseAPI } from "../base/base-clients";
import type { DebugResponse } from "~/lib/api/types/admin";

const prefix = "/api";

const routes = {
  ai: `${prefix}/admin/debug/ai`,
};

export class AdminDebugAPI extends BaseAPI {
  async debugAI(fileObject: Blob | File | undefined = undefined, fileName = "") {
    let formData: FormData | null = null;
    if (fileObject) {
      formData = new FormData();
      formData.append("image", fileObject);
      formData.append("extension", fileName.split(".").pop() ?? "");
    }

    return await this.requests.post<DebugResponse>(routes.ai, formData);
  }
}
