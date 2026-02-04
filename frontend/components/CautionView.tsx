import { Footer } from "./common/Footer";
import { BackToSafetyButton } from "./common/BackToSafetyButton";
import { ContinueButton } from "./common/ContinueButton";
import type { UrlReputationResponse } from "@/lib/api";

interface CautionViewProps {
  data: UrlReputationResponse;
  url: string;
}

/**
 * 경고 페이지 (WARNING 상태)
 * 피싱 및 스캠 의심 사이트 주의
 */
export function CautionView({ data, url }: CautionViewProps) {
  return (
    <div className="page-container page-caution">
      <main className="main-content">
        {/* 헤더 */}
        <header className="result-header">
          <h1 className="header-title header-caution">CAUTION</h1>
          <p className="header-subtitle">SUSPICIOUS SITE DETECTED</p>
        </header>

        {/* 아이콘 */}
        <div className="result-icon">
          <span className="icon-caution">⚠️</span>
        </div>

        {/* 타이틀 */}
        <h2 className="page-title">피싱 및 스캠 의심 사이트 주의</h2>
        <p className="page-description">
          본 사이트는 피싱 또는 스캠 가능성이 있어 이용시 주의가 필요합니다.
          <br />
          개인정보 및 결제 정보 입력 전 사이트의 안전성을 확인하기 바랍니다.
        </p>

        {/* 보안 체크리스트 */}
        <div className="info-card">
          <div className="info-header">
            <span className="info-icon">✓</span>
            <span className="info-title">보안 체크리스트</span>
          </div>
          <div className="info-body">
            <ol className="checklist">
              <li>
                접속한 웹사이트 주소가 공식 사이트와 일치하는지 다시 한 번
                확인하시기 바랍니다.
              </li>
              <li>
                금융 정보나 로그인 정보를 요구하는 출처가 불분명한 링크에
                주의하시기 바랍니다.
              </li>
              <li>
                브라우저 주소창에 자물쇠 아이콘이 표시되지 않거나 인증서 오류가
                발생하는지 확인하시기 바랍니다.
              </li>
            </ol>
          </div>
        </div>

        {/* 피해 예방 수칙 */}
        <div className="info-card">
          <div className="info-header">
            <span className="info-icon">🛡</span>
            <span className="info-title">피해 예방 수칙</span>
          </div>
          <div className="info-body">
            <div className="prevention-tips">
              <div className="tip-item">
                <h4>1. 정보 입력 금지</h4>
                <p>검증되지 않은 사이트에는 어떠한 정보도 입력하지 마십시오.</p>
              </div>
              <div className="tip-item">
                <h4>2. 경찰 신고</h4>
                <p>
                  피해 발생 시 즉시 112 또는 사이버범죄신고시스템으로
                  신고하십시오.
                </p>
              </div>
            </div>
          </div>
        </div>

        {data.description && (
          <div className="detail-card">
            <strong>분석 결과:</strong> {data.description}
          </div>
        )}

        {/* 버튼 그룹 */}
        <div className="button-group">
          <BackToSafetyButton />
          <ContinueButton url={url} />
        </div>
      </main>

      <Footer />
    </div>
  );
}
