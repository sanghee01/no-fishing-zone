"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1>오류 발생</h1>
      <div
        style={{
          color: "white",
          background: "#dc2626",
          padding: "1rem",
          borderRadius: "8px",
          marginTop: "1rem",
          marginBottom: "1rem",
        }}
      >
        <p>
          <strong>에러:</strong>{" "}
          {error.message || "알 수 없는 오류가 발생했습니다."}
        </p>
      </div>
      <button
        onClick={() => reset()}
        style={{
          padding: "0.5rem 1rem",
          background: "#3b82f6",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        다시 시도
      </button>
    </div>
  );
}
