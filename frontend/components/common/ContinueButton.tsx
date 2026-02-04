"use client";

interface ContinueButtonProps {
  url: string;
}

export function ContinueButton({ url }: ContinueButtonProps) {
  const handleClick = () => {
    window.location.href = url;
  };

  return (
    <button type="button" onClick={handleClick} className="btn btn-secondary">
      사이트 계속 이용하기
    </button>
  );
}
