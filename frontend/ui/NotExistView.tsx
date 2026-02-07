import { Flex, Box, Text, VStack } from "@devup-ui/react";
import { PageLayout } from "./layout/PageLayout";
import type { UrlReputationResponse } from "@/lib/api";
import { BackToSafetyButton } from "@/components/common/BackToSafetyButton";
import { Title } from "@/components/common/Title";
import { Header } from "@/components/common/Header";
import { BoxTitle } from "@/components/common/BoxTitle";
import { Unplug } from "lucide-react";

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
            title="DEAD"
            subTitle="SITE NOT REACHABLE"
            image="dead"
            color="var(--dead)"
          />
          <Title title="사이트에 연결할 수 없습니다." />
        </VStack>
      </PageLayout.Header>

      <PageLayout.Content>
        <VStack
          bg="$white"
          borderLeft="solid 7px $dead"
          borderRadius="0 20px 20px 0"
          boxShadow="0 3px 7px 0 rgba(0, 0, 0, 0.25)"
          gap="28px"
          p={["24px", null, null, null, "40px"]}
          w="100%"
          maxW="640px"
        >
          <BoxTitle
            title="CONNECTION FAILED"
            icon={
              <Box boxSize={["24px", null, null, null, "32px"]}>
                <Unplug
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
              해당 웹사이트는 현재 비활성화되어 있거나 서버에 연결할 수 없는
              상태입니다.
            </Text>
            <Text
              color="$text"
              fontSize={["14px", null, null, null, "16px"]}
              fontWeight="400"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              일시적인 장애이거나 폐쇄된 사이트일 수 있습니다. 접속하려는 URL을
              다시 한 번 확인해주세요.
            </Text>
            {data.description && (
              <Text
                color="$text"
                fontSize={["14px", null, null, null, "16px"]}
                fontWeight="400"
                lineHeight="1.6"
                wordBreak="keep-all"
              >
                상세 정보: {data.description}
              </Text>
            )}
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
