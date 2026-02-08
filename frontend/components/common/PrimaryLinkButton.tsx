import { Flex, Text } from "@devup-ui/react";
import React from "react";

interface PrimaryLinkButtonProps {
  label: string;
  href: string;
  icon?: React.ReactNode;
}

export function PrimaryLinkButton({
  label,
  href,
  icon,
}: PrimaryLinkButtonProps) {
  return (
    <Flex
      as="a"
      href={href}
      alignItems="center"
      justifyContent="center"
      gap="12px"
      bg="$primary"
      color="white"
      px={["32px", null, null, null, "48px"]}
      py={["16px", null, null, null, "20px"]}
      borderRadius="15px"
      boxShadow="0 5px 15px 0 rgba(0, 0, 0, 0.25)"
      textDecoration="none"
      cursor="pointer"
      _hover={{ bg: "$primaryDark" }}
    >
      {icon}
      <Text fontWeight="700" fontSize={["15px", null, null, null, "18px"]}>
        {label}
      </Text>
    </Flex>
  );
}
