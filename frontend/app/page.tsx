import { Suspense } from "react";
import { UrlReputationView } from "@/components/UrlReputationView";

export default function HomePage() {
  return (
    <Suspense fallback={<p>페이지 로딩 중...</p>}>
      <UrlReputationView />
    </Suspense>
  );
}
