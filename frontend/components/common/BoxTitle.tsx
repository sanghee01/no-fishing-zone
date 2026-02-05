import { Flex, Text } from "@devup-ui/react";
import type { ReactNode } from "react";

interface BoxTitleProps {
  title: string;
  icon: ReactNode;
  color?: string;
}

export function BoxTitle({ title, icon, color = "#1E293B" }: BoxTitleProps) {
  return (
    <Flex alignItems="center" gap="8px">
      {icon}
      <Text
        color={color}
        fontWeight="700"
        fontSize={["15px", null, null, null, "20px"]}
      >
        {title}
      </Text>
    </Flex>
  );
}
