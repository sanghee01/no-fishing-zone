"use client";

import { Box, Center, Image, Text, VStack } from "@devup-ui/react";
import { keyframes } from "@devup-ui/react";

const spin = keyframes({
  "0%": { transform: "rotate(0deg)" },
  "100%": { transform: "rotate(360deg)" },
});

/**
 * 원형 로딩 스피너 컴포넌트
 * 중앙에 방패 아이콘과 KNPA DIGITAL FORENSIC 텍스트
 * 외곽에 원형 프로그레스 애니메이션
 */
export function LoadingSpinner() {
  const progressColor = "#003366";
  const trackColor = "#E2E8F0";

  return (
    <Box pos="relative" boxSize={["240px", null, null, null, "300px"]}>
      {/* 바깥쪽 회전 아크 (SVG로 정밀 구현) */}
      <Box
        as="svg"
        viewBox="0 0 100 100"
        pos="absolute"
        top="0"
        left="0"
        boxSize="100%"
        animation={`${spin} 2s linear infinite`}
      >
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={trackColor}
          strokeWidth="2"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={progressColor}
          strokeWidth="4"
          strokeDasharray="70 200"
          strokeLinecap="round"
        />
      </Box>

      {/* 중앙 원형 영역 (레이어드 효과) */}
      <Center
        pos="absolute"
        top="50%"
        left="50%"
        transform="translate(-50%, -50%)"
        bg="#FFFFFF"
        borderRadius="50%"
        boxShadow="0 15px 35px rgba(0, 0, 0, 0.1), 0 5px 15px rgba(0, 0, 0, 0.05)"
        boxSize={["180px", null, null, null, "230px"]}
        flexDir="column"
        border="1px solid #F1F5F9"
      >
        <VStack alignItems="center" gap="16px">
          <Image
            src="/images/analyze.png"
            alt="KNPA Shield"
            boxSize={["70px", null, null, null, "90px"]}
            objectFit="contain"
          />
          <Text
            color="#003366"
            fontFamily="Noto Sans KR"
            fontSize="14px"
            fontWeight="700"
            letterSpacing="-0.02em"
            textAlign="center"
          >
            KNPA DIGITAL FORENSIC
          </Text>
        </VStack>
      </Center>
    </Box>
  );
}
