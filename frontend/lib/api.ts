import { createApi } from "@devup-api/fetch";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/";

export const api = createApi(baseURL);
