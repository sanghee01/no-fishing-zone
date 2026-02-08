import { Box, Flex, Text, VStack } from "@devup-ui/react";
import Image from "next/image";
import { PageLayout } from "./layout/PageLayout";
import type { UrlReputationResponse } from "@/lib/api";
import { PrimaryLinkButton } from "@/components/common/PrimaryLinkButton";
import { ContinueButton } from "@/components/common/ContinueButton";
import { Shield, CircleCheck } from "lucide-react";
import { Title } from "@/components/common/Title";
import { Header } from "@/components/common/Header";
import { BoxTitle } from "@/components/common/BoxTitle";

interface CautionViewProps {
  data: UrlReputationResponse;
  url: string;
}

export function CautionView({ data, url }: CautionViewProps) {
  return (
    <PageLayout variant="caution">
      <PageLayout.Header>
        <VStack alignItems="center" gap={["24px", null, null, null, "32px"]}>
          <Header
            title="CAUTION"
            subTitle="SUSPICIOUS SITE DETECTED"
            image="caution"
            color="var(--warning)"
          />

          <Title
            title="피싱 및 스캠 의심 사이트 주의"
            description={`본 사이트는 피싱 또는 스캠 가능성이 있어 이용시 주의가 필요합니다.\n개인정보 및 결제 정보 입력 전 사이트의 안전성을 확인하기 바랍니다.`}
          />
        </VStack>
      </PageLayout.Header>

      <PageLayout.Content>
        <VStack
          bg="$white"
          borderRadius="20px"
          boxShadow="0 3px 7px 0 rgba(0, 0, 0, 0.25)"
          gap="20px"
          p={["24px", null, null, null, "40px"]}
          w="100%"
          maxW="640px"
        >
          <BoxTitle
            title="보안 체크리스트"
            icon={
              <Box boxSize={["24px", null, null, null, "32px"]}>
                <CircleCheck
                  size="100%"
                  color="var(--white)"
                  fill="var(--warning)"
                  strokeWidth={1.5}
                />
              </Box>
            }
          />
          <VStack as="ol" gap="16px" pl="24px" m="0">
            <Text
              as="li"
              color="$text"
              fontSize="15px"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              접속한 웹사이트 주소가 공식 사이트와 일치하는지 다시 한 번
              확인하시기 바랍니다.
            </Text>
            <Text
              as="li"
              color="$text"
              fontSize="15px"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              금융 정보나 로그인 정보를 요구하는 출처가 불분명한 링크에
              주의하시기 바랍니다.
            </Text>
            <Text
              as="li"
              color="$text"
              fontSize="15px"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              브라우저 주소창에 자물쇠 아이콘이 표시되지 않거나 인증서 오류가
              발생하는지 확인하시기 바랍니다.
            </Text>
            {/* TODO: AI 프롬프팅 개선 후 적용 */}
            {/* <Text
              as="li"
              color="$text"
              fontSize="15px"
              lineHeight="1.6"
              wordBreak="keep-all"
            >
              상세 사유: {data.description}
            </Text> */}
          </VStack>
        </VStack>
        <VStack
          bg="#E9EEF4"
          borderRadius="20px"
          outline="solid 1px rgba(21, 53, 86, 0.3)"
          gap="24px"
          px={["24px", null, null, null, "32px"]}
          py={["20px", null, null, null, "24px"]}
          w="100%"
          maxW="640px"
        >
          <BoxTitle
            title="피해 예방 수칙"
            icon={
              <Box boxSize={["24px", null, null, null, "32px"]}>
                <Shield
                  size="100%"
                  color="var(--primary)"
                  fill="var(--primary)"
                  strokeWidth={1.5}
                />
              </Box>
            }
            color="var(--primary)"
          />
          <Flex gap="20px" flexDir={["column", null, null, null, "row"]}>
            <VStack
              bg="#FFFFFF"
              border="solid 1px rgba(21, 53, 86, 0.3)"
              borderRadius="10px"
              flex="1"
              p="20px"
              gap="8px"
            >
              <Text color="#003366" fontWeight="600" fontSize="16px">
                1. 정보 입력 금지
              </Text>
              <Text
                color="$text"
                fontSize="14px"
                fontWeight="350"
                wordBreak="keep-all"
              >
                검증되지 않은 사이트에는 어떠한 정보도 입력하지 마십시오.
              </Text>
            </VStack>
            <VStack
              bg="#FFFFFF"
              border="solid 1px rgba(21, 53, 86, 0.3)"
              borderRadius="10px"
              flex="1"
              p="20px"
              gap="8px"
            >
              <Text color="#003366" fontWeight="600" fontSize="16px">
                2. 경찰 신고
              </Text>
              <Text
                color="$text"
                fontSize="14px"
                fontWeight="350"
                wordBreak="keep-all"
              >
                피해 발생 시 즉시 112 또는 사이버범죄신고시스템으로
                신고하십시오.
              </Text>
            </VStack>
          </Flex>
        </VStack>

        <Flex
          gap="16px"
          flexWrap="wrap"
          justifyContent="center"
          w="100%"
          maxW="640px"
          flexDir={["column", null, null, null, "row"]}
        >
          <PrimaryLinkButton
            label="안전한 페이지로 돌아가기"
            href="https://www.google.com"
            icon={
              <Box position="relative" boxSize="24px">
                <Image
                  src="/images/shield-icon.png"
                  alt=""
                  fill
                  style={{ objectFit: "contain" }}
                />
              </Box>
            }
          />
          <ContinueButton url={url} color="white" />
        </Flex>
      </PageLayout.Content>

      <PageLayout.Footer />
    </PageLayout>
  );
}
