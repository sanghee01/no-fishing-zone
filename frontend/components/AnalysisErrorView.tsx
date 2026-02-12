import { Box, Button, Text, VStack } from "@devup-ui/react";

interface AnalysisErrorViewProps {
  errorCode: string;
  errorMessage: string;
  retryAfter: number | null;
  onRetry: () => void;
}

function getErrorIcon(errorCode: string): string {
  switch (errorCode) {
    case "AI_PROVIDER_OVERLOAD":
    case "AI_RATE_LIMIT_REACHED":
      return "⏳";
    case "AI_PROVIDER_ERROR":
    case "AI_SERVER_ERROR":
    case "AI_RESPONSE_PARSE_ERROR":
    case "UNKNOWN_SYSTEM_ERROR":
      return "⚠️";
    case "SSE_CONNECTION_LOST":
    case "NETWORK_ERROR":
      return "📡";
    default:
      return "❌";
  }
}

function getErrorTitle(errorCode: string): string {
  switch (errorCode) {
    case "AI_PROVIDER_OVERLOAD":
      return "AI 서버 과부하";
    case "AI_RATE_LIMIT_REACHED":
      return "분석 요청 제한";
    case "AI_PROVIDER_ERROR":
      return "AI 서비스 오류";
    case "AI_SERVER_ERROR":
      return "AI 서버 연결 실패";
    case "AI_RESPONSE_PARSE_ERROR":
      return "AI 응답 처리 오류";
    case "SSE_CONNECTION_LOST":
      return "연결 중단";
    case "NETWORK_ERROR":
      return "네트워크 오류";
    default:
      return "분석 실패";
  }
}

export function AnalysisErrorView({
  errorCode,
  errorMessage,
  retryAfter,
  onRetry,
}: AnalysisErrorViewProps) {
  return (
    <Box
      w="100%"
      display="flex"
      justifyContent="center"
      alignItems="center"
      py={["32px", null, null, null, "48px"]}
    >
      <VStack
        maxW="600px"
        w="90%"
        alignItems="center"
        gap="24px"
        bg="$white"
        p={["24px", null, null, null, "32px"]}
        borderRadius="16px"
        boxShadow="default"
      >
        <Text fontSize={["40px", null, null, null, "48px"]}>
          {getErrorIcon(errorCode)}
        </Text>
        <VStack alignItems="center" gap="8px">
          <Text
            fontSize={["20px", null, null, null, "24px"]}
            fontWeight="700"
            color="$black"
          >
            {getErrorTitle(errorCode)}
          </Text>

          <Text
            fontSize="16px"
            color="$textLight"
            textAlign="center"
            wordBreak="keep-all"
          >
            {errorMessage}
          </Text>

          {retryAfter && (
            <Text fontSize="14px" color="$gray500">
              {retryAfter}초 후 다시 시도해주세요
            </Text>
          )}
        </VStack>

        <Button
          onClick={onRetry}
          bg="$primary"
          color="$white"
          px="24px"
          py="12px"
          borderRadius="8px"
          fontWeight="600"
          _hover={{ bg: "$primaryLight", color: "$primary" }}
          transition="0.2s"
        >
          다시 분석하기
        </Button>
      </VStack>
    </Box>
  );
}
