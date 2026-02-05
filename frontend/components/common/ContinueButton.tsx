import { Flex, Text } from "@devup-ui/react";

interface ContinueButtonProps {
  url: string;
}

export function ContinueButton({ url }: ContinueButtonProps) {
  return (
    <Flex
      as="a"
      href={url}
      alignItems="center"
      justifyContent="center"
      bg="#FFFFFF"
      color="#64748B"
      px={["24px", null, null, null, "32px"]}
      py={["16px", null, null, null, "20px"]}
      borderRadius="15px"
      border="solid 1px #CBD5E1"
      boxShadow="0 4px 6px 0 rgba(0, 0, 0, 0.1)"
      textDecoration="none"
      cursor="pointer"
      _hover={{ bg: "#F8FAFC" }}
    >
      <Text fontWeight="700" fontSize={["15px", null, null, null, "18px"]}>
        사이트 계속 이용하기
      </Text>
    </Flex>
  );
}
