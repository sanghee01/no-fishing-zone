import { createApi } from "@devup-api/fetch";
import type { UrlReputationResponse, UrlReputationStatus } from "./types";

export type { UrlReputationResponse, UrlReputationStatus };

const getBaseURL = () => {
  // 서버 사이드
  if (typeof window === "undefined") {
    return process.env.API_BASE_URL || "http://api:8000";
  }
  // 클라이언트 사이드
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost/";
};

const baseURL = getBaseURL();

const api = createApi(baseURL);

/**
 * URL 평판 조회 API
 * @param url 조회할 URL
 * @returns URL 평판 정보 (데이터가 없으면 null 반환)
 */
export async function getUrlReputation(
  url: string,
): Promise<UrlReputationResponse | null> {
  const response = await api.get("getUrlReputation", {
    query: { url },
  });

  if (response.isOk && response.data) {
    return {
      url: response.data.url,
      description: response.data.description ?? null,
      score: response.data.score as number,
      status: response.data.status as UrlReputationStatus,
    };
  }

  if (response.response?.status === 404) {
    return null;
  }

  throw new Error("서버와의 통신 중 오류가 발생했습니다.");
}
