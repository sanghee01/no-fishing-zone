import { Flex, Image, Text } from "@devup-ui/react";

export function BackToSafetyButton() {
  return (
    <Flex
      as="a"
      href="https://www.google.com"
      alignItems="center"
      justifyContent="center"
      gap="12px"
      bg="$primary"
      color="white"
      px={["24px", null, null, null, "32px"]}
      py={["16px", null, null, null, "20px"]}
      borderRadius="15px"
      boxShadow="0 5px 15px 0 rgba(0, 0, 0, 0.25)"
      textDecoration="none"
      cursor="pointer"
      _hover={{ bg: "#00284F" }}
    >
      <Image src="/images/shield-icon.png" alt="" boxSize="24px" />
      <Text fontWeight="700" fontSize={["15px", null, null, null, "18px"]}>
        안전한 페이지로 돌아가기
      </Text>
    </Flex>
  );
}
