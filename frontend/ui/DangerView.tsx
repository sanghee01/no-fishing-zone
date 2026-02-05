import { Flex, Box, Text, VStack } from "@devup-ui/react";
import { PageLayout } from "./layout/PageLayout";
import type { UrlReputationResponse } from "@/lib/api";
import { BackToSafetyButton } from "@/components/common/BackToSafetyButton";
import { Title } from "@/components/common/Title";
import { Header } from "@/components/common/Header";
import { BoxTitle } from "@/components/common/BoxTitle";
import { TriangleAlert } from "lucide-react";

interface DangerViewProps {
  data: UrlReputationResponse;
}

export function DangerView({ data }: DangerViewProps) {
  return (
    <PageLayout variant="danger">
      <PageLayout.Header>
        <VStack alignItems="center" gap={["24px", null, null, null, "32px"]}>
          <Header
            title="WARNING"
            subTitle="ACCESS DENIED - PROHIBITED CONTENT"
            image="danger"
            color="var(--danger)"
          />
          <Title title="불법 유해 사이트 접속이 차단되었습니다." />
        </VStack>
      </PageLayout.Header>

      <PageLayout.Content>
        <VStack
          bg="$white"
          borderLeft="solid 7px $danger"
          borderRadius="0 20px 20px 0"
          boxShadow="0 3px 7px 0 rgba(0, 0, 0, 0.25)"
          gap="28px"
          p={["24px", null, null, null, "40px"]}
          w="100%"
          maxW="640px"
        >
          <BoxTitle
            title="RESTRICTED ACCESS"
            icon={
              <Box boxSize={["24px", null, null, null, "32px"]}>
                <TriangleAlert
                  size="100%"
                  color="var(--white)"
                  fill="var(--danger)"
                  strokeWidth={1.5}
                />
              </Box>
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
              이 웹페이지는 불법 또는 유해 콘텐츠를 포함하고 있어 관련 법령 및
              보안 기준에 따라 접속이 차단되었습니다.
            </Text>
            <Text
              color="$text"
              fontSize={["14px", null, null, null, "16px"]}
              fontWeight="400"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              해당 사이트 이용 시 법적 책임이 발생할 수 있으므로 더 이상의
              접근을 권장하지 않습니다.
            </Text>
            <Text
              color="$text"
              fontSize={["14px", null, null, null, "16px"]}
              fontWeight="400"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              상세 사유: {data.description}
            </Text>
          </VStack>
        </VStack>
        <Flex
          w="100%"
          maxW="640px"
          justifyContent="center"
          flexDir={["column", null, null, null, "row"]}
        >
          <BackToSafetyButton />
        </Flex>
      </PageLayout.Content>

      <PageLayout.Footer />
    </PageLayout>
  );
}
