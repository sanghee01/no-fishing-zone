"use client";

import { Box, Center, Image, Text, VStack } from "@devup-ui/react";
import { keyframes } from "@devup-ui/react";

const spin = keyframes({
  "0%": { transform: "rotate(0deg)" },
  "100%": { transform: "rotate(360deg)" },
});

const progressColor = "#003366";
const trackColor = "#E2E8F0";

export function LoadingSpinner() {
  return (
    <Box
      pos="relative"
      boxSize={["240px", null, null, null, "300px"]}
      mt={["60px", null, null, null, "0px"]}
    >
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
          strokeWidth="4"
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

      <Center
        pos="absolute"
        top="50%"
        left="50%"
        transform="translate(-50%, -50%)"
        bg="$white"
        borderRadius="50%"
        boxShadow="0 15px 35px rgba(0, 0, 0, 0.1), 0 5px 15px rgba(0, 0, 0, 0.05)"
        boxSize={["180px", null, null, null, "230px"]}
        flexDir="column"
        border="1px solid #F1F5F9"
      >
        <VStack alignItems="center" gap="8px">
          <Image
            src="/images/analyze.png"
            alt="analyze-icon"
            boxSize={["52px", null, null, null, "76px"]}
            objectFit="contain"
          />
          <Text
            color="#003366"
            fontFamily="Noto Sans KR"
            fontSize={["8px", null, null, null, "12px"]}
            fontWeight="700"
            letterSpacing="-0.02em"
            textAlign="center"
          >
            DIGITAL FORENSIC
          </Text>
        </VStack>
      </Center>
    </Box>
  );
}
