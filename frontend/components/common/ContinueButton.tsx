import { Flex, Text } from "@devup-ui/react";

type ButtonColor = "primary" | "white";
interface ContinueButtonProps {
  url: string;
  color?: ButtonColor;
}

export function ContinueButton({
  url,
  color = "primary",
}: ContinueButtonProps) {
  return (
    <Flex
      as="a"
      href={url}
      alignItems="center"
      justifyContent="center"
      bg={color === "primary" ? "var(--primary)" : "var(--white)"}
      color={color === "primary" ? "var(--white)" : "var(--primary)"}
      px={["32px", null, null, null, "60px"]}
      py={["16px", null, null, null, "20px"]}
      borderRadius="15px"
      border="solid 1px #CBD5E1"
      boxShadow="0 4px 6px 0 rgba(0, 0, 0, 0.1)"
      textDecoration="none"
      cursor="pointer"
      _hover={{
        bg: color === "primary" ? "var(--primaryDark)" : "var(--hoverGray)",
      }}
    >
      <Text fontWeight="700" fontSize={["15px", null, null, null, "18px"]}>
        사이트 계속 이용하기
      </Text>
    </Flex>
  );
}
