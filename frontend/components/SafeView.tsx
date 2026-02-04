import { Footer } from "./common/Footer";
import { ContinueButton } from "./common/ContinueButton";
import type { UrlReputationResponse } from "@/lib/api";

interface SafeViewProps {
  data: UrlReputationResponse;
  url: string;
}

/**
 * 안전 페이지 (SAFE 상태)
 * 테스트용 임시 페이지 - 실제 서비스에서는 즉시 리다이렉트
 */
export function SafeView({ data, url }: SafeViewProps) {
  return (
    <div className="page-container page-safe">
      <main className="main-content">
        {/* 헤더 */}
        <header className="result-header">
          <h1 className="header-title header-safe">SAFE</h1>
          <p className="header-subtitle">VERIFIED SECURE SITE</p>
        </header>

        {/* 아이콘 */}
        <div className="result-icon">
          <span className="icon-safe">✅</span>
        </div>

        {/* 타이틀 */}
        <h2 className="page-title">안전한 사이트입니다</h2>
        <p className="page-description">
          이 사이트는 보안 검증을 통과했습니다.
          <br />
          안심하고 이용하실 수 있습니다.
        </p>

        {/* 안전 정보 카드 */}
        <div className="info-card info-safe">
          <div className="info-header">
            <span className="info-icon">🛡</span>
            <span className="info-title">보안 검증 완료</span>
          </div>
          <div className="info-body">
            <p>
              <strong>URL:</strong> {data.url}
            </p>
            <p>
              <strong>안전 점수:</strong> {data.score}/100
            </p>
            {data.description && (
              <p>
                <strong>설명:</strong> {data.description}
              </p>
            )}
          </div>
        </div>

        {/* 버튼 */}
        <div className="button-group">
          <ContinueButton url={url} />
        </div>
      </main>

      <Footer />
    </div>
  );
}
