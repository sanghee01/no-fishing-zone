import {
  PageLayoutRoot,
  PageLayoutContent,
  PageLayoutFooter,
} from "@/ui/layout/PageLayout";
import { AnalysisView } from "@/ui/AnalysisView";
import { DangerView } from "@/ui/DangerView";
import { CautionView } from "@/ui/CautionView";
import { SafeView } from "@/ui/SafeView";
import { NotExistView } from "@/ui/NotExistView";
import { UrlInputForm } from "@/ui/UrlInputForm";
import { getUrlReputation } from "@/lib/api";
import { Flex } from "@devup-ui/react";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ url?: string }>;
}) {
  const { url } = await searchParams;
  const targetUrl = typeof url === "string" ? url : null;

  // URL이 없으면 URL 입력 화면
  if (!targetUrl) {
    return (
      <PageLayoutRoot>
        <PageLayoutContent>
          <Flex
            w="100%"
            h="100%"
            flex="1"
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
          >
            <UrlInputForm />
          </Flex>
        </PageLayoutContent>
        <PageLayoutFooter />
      </PageLayoutRoot>
    );
  }

  // 서버에서 DB 조회: 이미 분석된 결과가 있는지 확인
  const existingResult = await getUrlReputation(targetUrl);

  // 결과가 있으면 SSR로 즉시 렌더링 (CSR 불필요)
  if (existingResult) {
    switch (existingResult.status) {
      case "BLOCK":
        return <DangerView data={existingResult} />;
      case "WARNING":
        return <CautionView data={existingResult} url={targetUrl} />;
      case "SAFE":
        return <SafeView data={existingResult} url={targetUrl} />;
      case "DEAD":
        return <NotExistView data={existingResult} url={targetUrl} />;
    }
  }

  // 결과가 없으면 SSE 분석 시작 (CSR 필요)
  return <AnalysisView url={targetUrl} />;
}
