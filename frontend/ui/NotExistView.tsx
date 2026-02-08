import { Flex, Box, Text, VStack } from "@devup-ui/react";
import { PageLayout } from "./layout/PageLayout";
import type { UrlReputationResponse } from "@/lib/api";
import { PrimaryLinkButton } from "@/components/common/PrimaryLinkButton";
import { Title } from "@/components/common/Title";
import { Header } from "@/components/common/Header";
import { BoxTitle } from "@/components/common/BoxTitle";
import { Info } from "lucide-react";

interface NotExistViewProps {
  data: UrlReputationResponse;
  url: string;
}

export function NotExistView({ data }: NotExistViewProps) {
  return (
    <PageLayout variant="caution">
      <PageLayout.Header>
        <VStack alignItems="center" gap={["24px", null, null, null, "32px"]}>
          <Header
            title="NOT FOUND"
            subTitle="SITE NOT REACHABLE"
            image="not-found"
            color="var(--dead)"
          />
          <Title title="존재하지 않는 페이지입니다." />
        </VStack>
      </PageLayout.Header>

      <PageLayout.Content>
        <VStack
          bg="$white"
          borderLeft="solid 7px $dead"
          borderRadius="0 20px 20px 0"
          boxShadow="0 3px 7px 0 rgba(0, 0, 0, 0.25)"
          gap="20px"
          p={["24px", null, null, null, "40px"]}
          w="100%"
          maxW="640px"
        >
          <BoxTitle
            title="PAGE INFORMATION"
            icon={
              <Box boxSize={["24px", null, null, null, "32px"]}>
                <Info
                  size="100%"
                  color="var(--white)"
                  fill="var(--dead)"
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
              입력하신 주소가 올바르지 않거나, 요청하신 페이지가 이동 또는
              삭제되어 현재 찾을 수 없습니다.
            </Text>
            <Text
              color="$text"
              fontSize={["14px", null, null, null, "16px"]}
              fontWeight="400"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              주소를 다시 확인하거나 메인 페이지로 이동하여 이용하기 바랍니다.
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
                상세 정보: {data.description}
              </Text>
            )} */}
          </VStack>
        </VStack>
        <Flex
          w="100%"
          maxW="640px"
          justifyContent="center"
          flexDir={["column", null, null, null, "row"]}
        >
          <PrimaryLinkButton label="메인 페이지로 이동" href="/" />
        </Flex>
      </PageLayout.Content>

      <PageLayout.Footer />
    </PageLayout>
  );
}
