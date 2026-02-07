"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { VStack, Input, Button, Text } from "@devup-ui/react";

export function UrlInputForm() {
  const [url, setUrl] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    router.push(`/?url=${encodeURIComponent(url.trim())}`);
  };

  return (
    <VStack
      w="100%"
      maxW="600px"
      gap="24px"
      as="form"
      onSubmit={handleSearch}
      alignItems="center"
    >
      <VStack alignItems="center" gap="8px">
        <Text
          fontSize={["24px", null, null, null, "40px"]}
          fontWeight="800"
          color="$text"
          textAlign="center"
        >
          URL 안전 검사
        </Text>
        <Text
          fontSize={["16px", null, null, null, "20px"]}
          color="$textLight"
          textAlign="center"
        >
          조회할 URL을 입력해주세요.
        </Text>
      </VStack>

      <Input
        autoFocus
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com"
        w="100%"
        h={["50px", null, null, null, "60px"]}
        px="20px"
        bg="$white"
        borderRadius="12px"
        border="1px solid"
        borderColor="$gray"
        fontSize="16px"
        _focus={{
          outline: "none",
          border: "2px solid",
          borderColor: "$primary",
        }}
        _placeholder={{
          color: "$textLight",
        }}
      />

      <Button
        type="submit"
        bg="$primary"
        color="$white"
        w="100%"
        h={["50px", null, null, null, "60px"]}
        borderRadius="15px"
        fontSize={["16px", null, null, null, "18px"]}
        fontWeight="700"
        _hover={{ bg: "$primaryDark" }}
        cursor="pointer"
        disabled={!url.trim()}
      >
        검사하기
      </Button>
    </VStack>
  );
}
