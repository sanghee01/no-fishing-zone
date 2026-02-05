"use client";

import { useEffect, useState } from "react";
import { AnalysisView, type StepStatus } from "./AnalysisView";
import { DangerView } from "./DangerView";
import { CautionView } from "./CautionView";
import { SafeView } from "./SafeView";
import type { UrlReputationResponse } from "@/lib/api";

interface AnalysisPageProps {
  url: string;
}

interface AnalysisState {
  step1: StepStatus;
  step2: StepStatus;
  step3: StepStatus;
  result: UrlReputationResponse | null;
  error: string | null;
}

/**
 * 분석 흐름 관리 (Analysis Flow)
 * - 분석 진행 상태 (AnalysisView) 및 결과 (Safe/Caution/Danger) 렌더링
 * - SSE 연결 및 상태 관리 담당
 */
export function AnalysisPage({ url }: AnalysisPageProps) {
  const [state, setState] = useState<AnalysisState>({
    step1: "pending",
    step2: "pending",
    step3: "pending",
    result: null,
    error: null,
  });

  useEffect(() => {
    // SSE 연결
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

    // 클린업
    return () => {
      eventSource.close();
    };
  }, [url]);

  // 에러 상태
  if (state.error) {
    return (
      <div className="page-container page-error">
        <main className="main-content">
          <h1>오류 발생</h1>
          <p>{state.error}</p>
          <button onClick={() => window.location.reload()}>다시 시도</button>
        </main>
      </div>
    );
  }

  // 결과가 있으면 결과 페이지 표시
  if (state.result) {
    switch (state.result.status) {
      case "BLOCK":
        return <DangerView data={state.result} />;
      case "WARNING":
        return <CautionView data={state.result} url={url} />;
      case "SAFE":
        return <SafeView data={state.result} url={url} />;
    }
  }

  return (
    <AnalysisView step1={state.step1} step2={state.step2} step3={state.step3} />
  );
}
