import { Footer } from "./common/Footer";
import { BackToSafetyButton } from "./common/BackToSafetyButton";
import type { UrlReputationResponse } from "@/lib/api";

interface DangerViewProps {
  data: UrlReputationResponse;
}

/**
 * 위험 페이지 (BLOCK 상태)
 * 불법 유해 사이트 차단 안내
 */
export function DangerView({ data }: DangerViewProps) {
  return (
    <div className="page-container page-danger">
      <main className="main-content">
        {/* 헤더 */}
        <header className="result-header">
          <h1 className="header-title header-danger">WARNING</h1>
          <p className="header-subtitle">ACCESS DENIED - PROHIBITED CONTENT</p>
        </header>

        {/* 아이콘 */}
        <div className="result-icon">
          <span className="icon-danger">🚨</span>
        </div>

        {/* 타이틀 */}
        <h2 className="page-title">불법 유해 사이트 접속이 차단되었습니다.</h2>

        {/* 경고 카드 */}
        <div className="alert-card alert-danger">
          <div className="alert-header">
            <span className="alert-icon">⚠</span>
            <span className="alert-title">RESTRICTED ACCESS</span>
          </div>
          <div className="alert-body">
            <p>
              이 웹페이지는 불법 또는 유해 콘텐츠를 포함하고 있어 관련 법령 및
              보안 기준에 따라 접속이 차단되었습니다.
            </p>
            <p>
              해당 사이트 이용 시 법적 책임이 발생할 수 있으므로 더 이상의
              접근을 권장하지 않습니다.
            </p>
            {data.description && (
              <p className="alert-description">
                <strong>상세:</strong> {data.description}
              </p>
            )}
          </div>
        </div>

        {/* 버튼 */}
        <div className="button-group">
          <BackToSafetyButton />
        </div>
      </main>

      <Footer />
    </div>
  );
}
