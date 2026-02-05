"use client";

import { PageLayout } from "./layout/PageLayout";
import { LoadingSpinner } from "@/components/analysisView/LoadingSpinner";
import { ChecklistCard } from "@/components/analysisView/ChecklistCard";
import {
  ChecklistItem,
  type StepStatus,
} from "@/components/analysisView/ChecklistItem";
import { Title } from "@/components/common/Title";

export type { StepStatus };

interface AnalysisViewProps {
  step1: StepStatus;
  step2: StepStatus;
  step3: StepStatus;
}

export function AnalysisView({ step1, step2, step3 }: AnalysisViewProps) {
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
