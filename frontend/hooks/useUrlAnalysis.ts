"use client";

import { useCallback, useEffect, useState } from "react";
import type { UrlReputationResponse } from "@/lib/api";

export type StepStatus = "pending" | "in_progress" | "completed";

export interface AnalysisState {
  step1: StepStatus;
  step2: StepStatus;
  step3: StepStatus;
  result: UrlReputationResponse | null;
  error: string | null;
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
  });

  const retry = useCallback(() => {
    setState({
      step1: "pending",
      step2: "pending",
      step3: "pending",
      result: null,
      error: null,
    });
    setRetryCount((prev) => prev + 1);
  }, []);

  useEffect(() => {
    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const eventSource = new EventSource(
      `${apiBaseUrl}/url-reputations/analyze-stream?url=${encodeURIComponent(url)}`,
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // 진행 상태 업데이트
        if (data.step !== undefined) {
          setState((prev) => {
            const newState = { ...prev };

            // 해당 단계까지 완료 처리
            if (data.step >= 1) {
              newState.step1 =
                data.step === 1 && data.status === "in_progress"
                  ? "in_progress"
                  : "completed";
            }
            if (data.step >= 2) {
              newState.step2 =
                data.step === 2 && data.status === "in_progress"
                  ? "in_progress"
                  : data.step > 2
                    ? "completed"
                    : prev.step2;
            }
            if (data.step >= 3) {
              newState.step3 =
                data.step === 3 && data.status === "in_progress"
                  ? "in_progress"
                  : data.step > 3
                    ? "completed"
                    : prev.step3;
            }

            // 현재 단계를 in_progress로 설정
            if (data.status === "in_progress") {
              if (data.step === 1) newState.step1 = "in_progress";
              if (data.step === 2) newState.step2 = "in_progress";
              if (data.step === 3) newState.step3 = "in_progress";
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

        // 완료 이벤트
        if (data.done) {
          eventSource.close();
        }
      } catch (e) {
        console.error("SSE parse error:", e);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      setState((prev) => ({
        ...prev,
        error: "서버 연결에 실패했습니다. 다시 시도해주세요.",
      }));
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [url, retryCount]);

  return {
    ...state,
    retry,
  };
}
