"use client";

export function BackToSafetyButton() {
  const handleClick = () => {
    // 브라우저 히스토리가 있으면 뒤로가기, 없으면 창 닫기 시도
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.close();
    }
  };

  return (
    <button type="button" onClick={handleClick} className="btn btn-primary">
      <span className="btn-icon">↩</span>
      안전한 페이지로 돌아가기
    </button>
  );
}
