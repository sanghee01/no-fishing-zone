"use client";

import { ErrorView } from "@/components/common/ErrorView";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorView
      message={error.message || "알 수 없는 오류가 발생했습니다."}
      onRetry={() => reset()}
    />
  );
}
