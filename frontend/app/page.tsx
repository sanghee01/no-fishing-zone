import {
  PageLayoutRoot,
  PageLayoutContent,
  PageLayoutFooter,
} from "@/ui/layout/PageLayout";
import { AnalysisView } from "@/ui/AnalysisView";
import { DangerView } from "@/ui/DangerView";
import { CautionView } from "@/ui/CautionView";
import { SafeView } from "@/ui/SafeView";
import { getUrlReputation } from "@/lib/api";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ url?: string }>;
}) {
  const { url } = await searchParams;
  const targetUrl = typeof url === "string" ? url : null;

  // URL이 없으면 안내 메시지
  if (!targetUrl) {
    return (
      <PageLayoutRoot>
        <PageLayoutContent>
          <div style={{ marginTop: "100px", textAlign: "center" }}>
            <h1
              style={{
                fontSize: "2.5rem",
                fontWeight: "800",
                marginBottom: "1rem",
                color: "#1E293B",
              }}
            >
              URL 평판 조회
            </h1>
            <p style={{ fontSize: "1.2rem", color: "#64748B" }}>
              조회할 URL을 입력해주세요.
            </p>
            <p style={{ marginTop: "2rem", color: "#94A3B8" }}>
              예시: ?url=https://example.com
            </p>
          </div>
        </PageLayoutContent>
        <PageLayoutFooter />
      </PageLayoutRoot>
    );
  }

  // 서버에서 DB 조회: 이미 분석된 결과가 있는지 확인
  const existingResult = await getUrlReputation(targetUrl);

  // 결과가 있으면 SSR로 즉시 렌더링 (CSR 불필요)
  if (existingResult) {
    switch (existingResult.status) {
      case "BLOCK":
        return <DangerView data={existingResult} />;
      case "WARNING":
        return <CautionView data={existingResult} url={targetUrl} />;
      case "SAFE":
        return <SafeView data={existingResult} url={targetUrl} />;
    }
  }

  // 결과가 없으면 SSE 분석 시작 (CSR 필요)
  return <AnalysisView url={targetUrl} />;
}
