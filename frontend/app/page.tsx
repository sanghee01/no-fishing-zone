import {
  PageLayoutRoot,
  PageLayoutContent,
  PageLayoutFooter,
} from "@/ui/layout/PageLayout";
import { AnalysisPage } from "@/ui/AnalysisPage";

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

  // URL이 있으면 분석 흐름(AnalysisPage) 시작
  return <AnalysisPage url={targetUrl} />;
}
