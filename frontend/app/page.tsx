"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { api } from "@/lib/api";

type UrlReputationResponse = {
  url: string;
  description: string | null;
  score: number;
  status: "SAFE" | "WARNING" | "BLOCK";
};

function UrlReputationContent() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<UrlReputationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const urlParam = searchParams.get("url");

  useEffect(() => {
    if (!urlParam) return;

    const fetchUrlReputation = async () => {
      setLoading(true);
      setError(null);
      setNotFound(false);
      setData(null);

      try {
        const response = await api.get("getUrlReputation", {
          query: { url: urlParam },
        });

        if (response.isOk && response.data) {
          setData({
            url: response.data.url,
            description: response.data.description ?? null,
            score: response.data.score as number,
            status: response.data.status as "SAFE" | "WARNING" | "BLOCK",
          });
        } else if (response.response?.status === 404) {
          setNotFound(true);
        } else {
          setError("서버와의 통신 중 오류가 발생했습니다.");
        }
      } catch (err) {
        console.error("Fetch error:", err);
        setError("API 호출 중 예외가 발생했습니다.");
      } finally {
        setLoading(false);
      }
    };

    fetchUrlReputation();
  }, [urlParam]);

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1>URL 평판 조회</h1>

      <div style={{ marginTop: "1rem", marginBottom: "2rem" }}>
        <p>
          <strong>조회 URL:</strong> {urlParam || "없음"}
        </p>
        {!urlParam && (
          <p style={{ color: "#666", fontSize: "0.9rem" }}>
            예시: ?url=https://example.com
          </p>
        )}
      </div>

      {loading && <p>데이터를 불러오는 중입니다...</p>}

      {error && (
        <div
          style={{
            color: "white",
            background: "#dc2626",
            padding: "1rem",
            borderRadius: "8px",
            marginTop: "1rem",
          }}
        >
          <p>
            <strong>에러:</strong> {error}
          </p>
        </div>
      )}

      {notFound && !loading && (
        <div
          style={{
            background: "#f3f4f6",
            border: "1px solid #d1d5db",
            padding: "1.5rem",
            borderRadius: "8px",
            marginTop: "1rem",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>🔍</p>
          <p>
            <strong>&quot;{urlParam}&quot;</strong>에 대한 평판 정보가 아직
            등록되지 않았습니다.
          </p>
          <p style={{ color: "#666", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            AI 에이전트가 곧 이 URL을 분석할 예정입니다.
          </p>
        </div>
      )}

      {data && !loading && (
        <div style={{ marginTop: "1rem" }}>
          <h2>평판 정보</h2>
          <div
            style={{
              background:
                data.status === "BLOCK"
                  ? "#fee2e2"
                  : data.status === "WARNING"
                    ? "#fef3c7"
                    : "#dcfce7",
              border: `2px solid ${
                data.status === "BLOCK"
                  ? "#dc2626"
                  : data.status === "WARNING"
                    ? "#f59e0b"
                    : "#16a34a"
              }`,
              padding: "1.5rem",
              borderRadius: "8px",
              marginTop: "1rem",
            }}
          >
            <div style={{ marginBottom: "1rem" }}>
              <strong>URL:</strong> {data.url}
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <strong>평판 점수:</strong> {data.score} / 100
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <strong>상태:</strong>{" "}
              <span
                style={{
                  color:
                    data.status === "BLOCK"
                      ? "#dc2626"
                      : data.status === "WARNING"
                        ? "#f59e0b"
                        : "#16a34a",
                  fontWeight: "bold",
                }}
              >
                {data.status === "BLOCK"
                  ? "🚫 차단 권장"
                  : data.status === "WARNING"
                    ? "⚠️ 경고"
                    : "✅ 안전"}
              </span>
            </div>

            {data.description && (
              <div>
                <strong>설명:</strong>
                <p style={{ marginTop: "0.5rem" }}>{data.description}</p>
              </div>
            )}
          </div>

          <details style={{ marginTop: "2rem" }}>
            <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
              원본 JSON 데이터
            </summary>
            <pre
              style={{
                background: "#f5f5f5",
                padding: "1rem",
                borderRadius: "4px",
                overflow: "auto",
                marginTop: "0.5rem",
              }}
            >
              {JSON.stringify(data, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<p>페이지 로딩 중...</p>}>
      <UrlReputationContent />
    </Suspense>
  );
}
