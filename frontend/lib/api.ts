import { createApi } from "@devup-api/fetch";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/";

const api = createApi(baseURL);

export type UrlReputationStatus = "SAFE" | "WARNING" | "BLOCK";

export interface UrlReputationResponse {
  url: string;
  description: string | null;
  score: number;
  status: UrlReputationStatus;
}

/**
 * URL 평판 조회 API
 * @param url 조회할 URL
 * @returns URL 평판 정보
 */
export async function getUrlReputation(url: string): Promise<{
  data: UrlReputationResponse | null;
  notFound: boolean;
  error: string | null;
}> {
  try {
    const response = await api.get("getUrlReputation", {
      query: { url },
    });

    if (response.isOk && response.data) {
      return {
        data: {
          url: response.data.url,
          description: response.data.description ?? null,
          score: response.data.score as number,
          status: response.data.status as UrlReputationStatus,
        },
        notFound: false,
        error: null,
      };
    }

    if (response.response?.status === 404) {
      return {
        data: null,
        notFound: true,
        error: null,
      };
    }

    return {
      data: null,
      notFound: false,
      error: "서버와의 통신 중 오류가 발생했습니다.",
    };
  } catch (err) {
    console.error("Fetch error:", err);
    return {
      data: null,
      notFound: false,
      error: "API 호출 중 예외가 발생했습니다.",
    };
  }
}
