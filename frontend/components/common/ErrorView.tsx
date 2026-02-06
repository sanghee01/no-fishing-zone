"use client";

import { Box, Button, Text, VStack } from "@devup-ui/react";
import { AlertCircle } from "lucide-react";

interface ErrorViewProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorView({
  title = "오류 발생",
  message,
  onRetry,
}: ErrorViewProps) {
  return (
    <Box
      w="100%"
      h="100vh"
      display="flex"
      justifyContent="center"
      alignItems="center"
      bg="$background"
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
        <Box color="$danger">
          <AlertCircle size={48} />
        </Box>
        <VStack alignItems="center" gap="8px">
          <Text
            fontSize={["20px", null, null, null, "24px"]}
            fontWeight="700"
            color="$black"
          >
            {title}
          </Text>
          <Text
            fontSize="16px"
            color="$textLight"
            textAlign="center"
            wordBreak="keep-all"
          >
            {message}
          </Text>
        </VStack>
        {onRetry && (
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
            다시 시도
          </Button>
        )}
      </VStack>
    </Box>
  );
}
