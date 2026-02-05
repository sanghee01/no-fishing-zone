import { Box, Flex, Text, VStack } from "@devup-ui/react";
import { CheckCircle } from "lucide-react";
import { PageLayout } from "./layout/PageLayout";
import { Title } from "@/components/common/Title";
import type { UrlReputationResponse } from "@/lib/api";
import { ContinueButton } from "@/components/common/ContinueButton";
import { Header } from "@/components/common/Header";
import { BoxTitle } from "@/components/common/BoxTitle";

interface SafeViewProps {
  data: UrlReputationResponse;
  url: string;
}

/**
 * 테스트용 임시 페이지 - 실제 서비스에서는 즉시 리다이렉트
 */
export function SafeView({ data, url }: SafeViewProps) {
  return (
    <PageLayout>
      <PageLayout.Header>
        <VStack alignItems="center" gap={["24px", null, null, null, "32px"]}>
          <Header
            title="SAFE"
            subTitle="SAFE - SAFE SITE"
            image="safe"
            color="var(--safe)"
          />
          <Title
            title="안전한 사이트입니다"
            description="이 사이트는 보안 검증을 통과했습니다. 안심하고 이용하실 수 있습니다."
          />
        </VStack>
      </PageLayout.Header>

      <PageLayout.Content>
        <VStack
          bg="$white"
          border="solid 1px"
          borderColor="$safe"
          borderRadius="16px"
          p={["24px", null, null, null, "32px"]}
          w="100%"
          maxW="600px"
          gap="20px"
        >
          <BoxTitle
            title="보안 검증 완료"
            icon={
              <Box boxSize={["24px", null, null, null, "32px"]}>
                <CheckCircle
                  size="100%"
                  color="var(--safe)"
                  strokeWidth={1.5}
                />
              </Box>
            }
            color="var(--safe)"
          />
          <VStack gap="12px">
            <Flex justifyContent="space-between">
              <Text color="$black" fontWeight="700">
                URL:
              </Text>
              <Text color="$blackLight">{data.url}</Text>
            </Flex>
            <Flex justifyContent="space-between">
              <Text color="$black" fontWeight="700">
                안전 점수:
              </Text>
              <Text color="$safe" fontWeight="700">
                {data.score}/100
              </Text>
            </Flex>
            {data.description && (
              <Flex justifyContent="space-between">
                <Text color="$black" fontWeight="700">
                  설명:
                </Text>
                <Text color="$blackLight">{data.description}</Text>
              </Flex>
            )}
          </VStack>
        </VStack>

        <Flex
          w="100%"
          justifyContent="center"
          flexDir={["column", null, null, null, "row"]}
        >
          <ContinueButton url={url} />
        </Flex>
      </PageLayout.Content>

      <PageLayout.Footer />
    </PageLayout>
  );
}
