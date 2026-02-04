import { AnalysisPage } from "@/components/AnalysisPage";

/**
 * 메인 페이지 - URL 파라미터를 추출하여 AnalysisPage에 전달
 * 서버 컴포넌트
 */
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
      <div className="page-container">
        <main className="main-content">
          <h1>URL 평판 조회</h1>
          <p>조회할 URL을 입력해주세요.</p>
          <p className="hint">예시: ?url=https://example.com</p>
        </main>
      </div>
    );
  }

  // URL이 있으면 분석 페이지 표시
  return <AnalysisPage url={targetUrl} />;
}
