import { Box, Flex, Text, VStack } from "@devup-ui/react";
import { Check } from "lucide-react";
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

export function SafeView({ data, url }: SafeViewProps) {
  return (
    <PageLayout>
      <PageLayout.Header>
        <VStack alignItems="center" gap={["24px", null, null, null, "32px"]}>
          <Header
            title="SAFE"
            subTitle="VERIFIED CONTENT - ACCESS GRANTED"
            image="safe2"
            color="var(--safe)"
          />
          <Title title="안전한 사이트입니다." description="" />
        </VStack>
      </PageLayout.Header>

      <PageLayout.Content>
        <Flex
          bg="$white"
          borderTopLeftRadius="4px"
          borderBottomLeftRadius="4px"
          borderTopRightRadius="20px"
          borderBottomRightRadius="20px"
          overflow="hidden"
          boxShadow="0 3px 7px 0 rgba(0, 0, 0, 0.25)"
          w="100%"
          maxW="640px"
        >
          <Box w="8px" bg="$safe" flexShrink={0} />
          <VStack gap="20px" p={["24px", null, null, null, "40px"]} flex={1}>
            <BoxTitle
              title="VERIFIED ACCESS"
              icon={
                <Flex
                  alignItems="center"
                  justifyContent="center"
                  boxSize={["24px", null, null, null, "28px"]}
                  borderRadius="50%"
                  bg="$safe"
                  flexShrink={0}
                >
                  <Check size="60%" color="white" strokeWidth={3} />
                </Flex>
              }
            />
            <VStack gap="16px">
              <Text
                color="$text"
                fontSize={["14px", null, null, null, "16px"]}
                fontWeight="400"
                lineHeight="1.6"
                wordBreak="keep-all"
              >
                이 웹페이지는 보안 검사 결과 위험 요소 및 유해 콘텐츠가 없는
                것으로 확인되었으며, 관련 보안 기준을 충족합니다.{" "}
              </Text>
              <Text
                color="$text"
                fontSize={["14px", null, null, null, "16px"]}
                fontWeight="400"
                lineHeight="1.6"
                wordBreak="keep-all"
              >
                사용자 보호를 위해 실시간 보호 스캔이 적용되고 있으며, 현재
                페이지는 안전하게 이용할 수 있습니다.
              </Text>
              {/* TODO: AI 프롬프팅 개선 후 적용 */}
              {/* {data.description && (
                <Text
                  color="$text"
                  fontSize={["14px", null, null, null, "16px"]}
                  fontWeight="400"
                  lineHeight="1.6"
                  wordBreak="keep-all"
                >
                  검사 결과: {data.description}
                </Text>
              )} */}
            </VStack>
          </VStack>
        </Flex>

        <Flex
          w="100%"
          maxW="640px"
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
