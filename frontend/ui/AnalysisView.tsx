"use client";

import { useUrlAnalysis } from "@/hooks/useUrlAnalysis";
import { PageLayout } from "./layout/PageLayout";
import { LoadingSpinner } from "@/components/analysisView/LoadingSpinner";
import { ChecklistCard } from "@/components/analysisView/ChecklistCard";
import {
  ChecklistItem,
  type StepStatus,
} from "@/components/analysisView/ChecklistItem";
import { Title } from "@/components/common/Title";
import { DangerView } from "./DangerView";
import { CautionView } from "./CautionView";
import { SafeView } from "./SafeView";
import { NotExistView } from "./NotExistView";
import { ErrorView } from "@/components/common/ErrorView";

export type { StepStatus };

interface AnalysisViewProps {
  url: string;
}

export function AnalysisView({ url }: AnalysisViewProps) {
  const { step1, step2, step3, result, error, retry } = useUrlAnalysis(url);

  if (error) {
    return <ErrorView message={error} onRetry={retry} />;
  }

  if (result) {
    switch (result.status) {
      case "BLOCK":
        return <DangerView data={result} />;
      case "WARNING":
        return <CautionView data={result} url={url} />;
      case "SAFE":
        return <SafeView data={result} url={url} />;
      case "DEAD":
        return <NotExistView data={result} url={url} />;
    }
  }

  return (
    <PageLayout>
      <PageLayout.Header>
        <LoadingSpinner />
      </PageLayout.Header>

      <PageLayout.Content>
        <Title
          title="데이터를 수집 중입니다..."
          description="보안 수사 및 분석을 위해 정보를 정리하고 있습니다."
        />
        <ChecklistCard>
          <ChecklistItem label="접속 기록 분석 중" status={step1} />
          <ChecklistItem label="불법 데이터 식별 중" status={step2} />
          <ChecklistItem label="증거 자료 수집 중" status={step3} />
        </ChecklistCard>
      </PageLayout.Content>

      <PageLayout.Footer />
    </PageLayout>
  );
}
