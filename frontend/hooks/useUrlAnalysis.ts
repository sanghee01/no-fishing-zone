"use client";

import { useCallback, useEffect, useState } from "react";
import type { UrlReputationResponse } from "@/lib/api";
import { fetchEventSource } from "@microsoft/fetch-event-source";

export type StepStatus = "pending" | "in_progress" | "completed";

/**
 * URL 분석 상태
 */
export interface AnalysisState {
  step1: StepStatus; // DB 조회
  step2: StepStatus; // AI 분석
  step3: StepStatus; // 결과 저장
  result: UrlReputationResponse | null;
  error: string | null;
  errorCode: string | null;
  retryAfter: number | null;
}

interface UseUrlAnalysisResult extends AnalysisState {
  retry: () => void;
}

/**
 * URL 분석 SSE 연결을 관리하는 커스텀 훅
 * - EventSource를 통해 서버와 SSE 연결
 * - 진행 상태(step1, step2, step3) 및 최종 결과 관리
 */
export function useUrlAnalysis(url: string): UseUrlAnalysisResult {
  const [retryCount, setRetryCount] = useState(0);
  const [state, setState] = useState<AnalysisState>({
    step1: "pending",
    step2: "pending",
    step3: "pending",
    result: null,
    error: null,
    errorCode: null,
    retryAfter: null,
  });

  const retry = useCallback(() => {
    setState({
      step1: "pending",
      step2: "pending",
      step3: "pending",
      result: null,
      error: null,
      errorCode: null,
      retryAfter: null,
    });
    setRetryCount((prev) => prev + 1);
  }, []);

  useEffect(() => {
    let apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    // 환경변수가 없으면 현재 오리진 사용
    if (!apiBaseUrl) {
      apiBaseUrl = typeof window !== "undefined" ? window.location.origin : "";
    }

    // 끝에 붙은 슬래시 제거 (이중 슬래시 //url-reputations... 방지)
    if (apiBaseUrl.endsWith("/")) {
      apiBaseUrl = apiBaseUrl.slice(0, -1);
    }

    const controller = new AbortController();

    async function startAnalysis() {
      try {
        await fetchEventSource(`${apiBaseUrl}/url-reputations/analyze-stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url }),
          signal: controller.signal,
          onmessage(event) {
            // 빈 메시지는 무시
            if (!event.data) {
              return;
            }

            try {
              const data = JSON.parse(event.data);

              if (data.status === "error") {
                setState((prev) => ({
                  ...prev,
                  error: data.error_message || "분석 중 오류가 발생했습니다.",
                  errorCode: data.error_code || "UNKNOWN_SYSTEM_ERROR",
                  retryAfter: data.retry_after || null,
                }));

                // 에러 발생 시 연결 종료
                if (data.done) {
                  controller.abort();
                }
                return;
              }

              // 진행 상태 업데이트
              if (data.step !== undefined) {
                setState((prev) => {
                  const newState = { ...prev };

                  if (data.step === 1) {
                    newState.step1 = data.status as StepStatus;
                  } else if (data.step === 2) {
                    if (prev.step1 === "in_progress") {
                      newState.step1 = "completed";
                    }
                    newState.step2 = data.status as StepStatus;
                  } else if (data.step === 3) {
                    if (prev.step1 === "in_progress") {
                      newState.step1 = "completed";
                    }
                    if (prev.step2 === "in_progress") {
                      newState.step2 = "completed";
                    }
                    newState.step3 = data.status as StepStatus;
                  }

                  // 결과가 있으면 저장
                  if (data.result) {
                    newState.result = data.result;
                    newState.step1 = "completed";
                    newState.step2 = "completed";
                    newState.step3 = "completed";
                  }

                  return newState;
                });
              }

              // 완료 이벤트 (서버에서 done: true를 보내면 연결 종료)
              if (data.done) {
                controller.abort();
              }
            } catch (e) {
              console.error("SSE parse error. Raw data:", event.data, e);
            }
          },
          onerror(err) {
            console.error("SSE error:", err);

            setState((prev) => ({
              ...prev,
              error: "서버 연결이 중단되었습니다. 다시 시도해주세요.",
              errorCode: "SSE_CONNECTION_LOST",
              retryAfter: null,
            }));

            throw err;
          },
        });
      } catch (err) {
        if (!controller.signal.aborted) {
          console.error("Analysis failed", err);
        }
      }
    }

    startAnalysis();

    return () => {
      controller.abort();
    };
  }, [url, retryCount]);

  return {
    ...state,
    retry,
  };
}
