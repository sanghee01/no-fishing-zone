import { Footer } from "./common/Footer";

export type StepStatus = "pending" | "in_progress" | "completed";

interface LoadingViewProps {
  step1: StepStatus;
  step2: StepStatus;
  step3: StepStatus;
}

/**
 * 로딩 뷰 - 3단계 체크리스트
 * 1. 접속 기록 분석 중
 * 2. 불법 데이터 식별 중
 * 3. 증거 자료 수집 중
 */
export function LoadingView({ step1, step2, step3 }: LoadingViewProps) {
  return (
    <div className="page-container">
      <main className="main-content">
        {/* 로고 영역 */}
        <div className="logo-section">
          <div className="logo-circle">
            <div className="logo-inner">
              <span className="logo-icon">🛡️</span>
              <span className="logo-text">KNPA DIGITAL FORENSIC</span>
            </div>
          </div>
        </div>

        {/* 타이틀 */}
        <h1 className="page-title">데이터를 수집 중입니다...</h1>
        <p className="page-description">
          보안 수사 및 분석을 위해 정보를 정리하고 있습니다.
        </p>

        {/* 체크리스트 */}
        <div className="checklist-card">
          <ChecklistItem label="접속 기록 분석 중" status={step1} />
          <ChecklistItem label="불법 데이터 식별 중" status={step2} />
          <ChecklistItem label="증거 자료 수집 중" status={step3} />
        </div>

        {/* 보안 안내 */}
        <div className="security-notice">
          <span className="security-icon">🔒</span>
          <span>암호화된 보안 연결이 활성화되어 있습니다.</span>
        </div>
      </main>

      <Footer />
    </div>
  );
}

interface ChecklistItemProps {
  label: string;
  status: StepStatus;
}

function ChecklistItem({ label, status }: ChecklistItemProps) {
  return (
    <div className="checklist-item">
      <div className="checklist-icon">
        {status === "completed" && <span className="icon-check">✓</span>}
        {status === "in_progress" && <span className="icon-loading">◌</span>}
        {status === "pending" && <span className="icon-pending">○</span>}
      </div>
      <span className="checklist-label">{label}</span>
      <span className="checklist-status">
        {status === "completed" && "완료"}
        {status === "in_progress" && "진행 중"}
        {status === "pending" && "대기"}
      </span>
    </div>
  );
}
