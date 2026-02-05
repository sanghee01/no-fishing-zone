import { Text, VStack } from "@devup-ui/react";

interface TitleProps {
  title: string;
  description?: string;
}

export function Title({ title, description }: TitleProps) {
  return (
    <VStack alignItems="center" gap="12px">
      <Text
        color="#1E293B"
        fontSize={["24px", null, null, null, "36px"]}
        fontWeight="800"
        textAlign="center"
        wordBreak="keep-all"
        letterSpacing="-0.02em"
        px={["32px", null, null, null, "0"]}
        style={{ textWrap: "balance" }}
      >
        {title}
      </Text>
      <Text
        color="#64748B"
        fontSize={["14px", null, null, null, "18px"]}
        fontWeight="400"
        textAlign="center"
        wordBreak="keep-all"
        lineHeight="1.6"
        whiteSpace="pre-line"
        px={["32px", null, null, null, "0"]}
        style={{ textWrap: "balance" }}
      >
        {description}
      </Text>
    </VStack>
  );
}
