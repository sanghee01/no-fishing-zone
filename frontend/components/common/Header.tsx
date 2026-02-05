import { Image, Text, VStack } from "@devup-ui/react";

interface HeaderProps {
  title: string;
  subTitle: string;
  image: string;
  color: string;
}

export function Header({ title, subTitle, image, color }: HeaderProps) {
  return (
    <VStack alignItems="center" gap={["24px", null, null, null, "40px"]}>
      <VStack alignItems="center">
        <Text
          color={color}
          fontSize={["36px", null, null, null, "56px"]}
          fontWeight="800"
          letterSpacing="0.25em"
          textAlign="center"
        >
          {title}
        </Text>
        <Text
          color={color}
          textAlign="center"
          fontSize={["13px", null, null, null, "24px"]}
          fontWeight="600"
          letterSpacing="0.1em"
        >
          {subTitle}
        </Text>
      </VStack>
      <Image
        src={`/images/${image}.png`}
        alt="Caution Triangle"
        w={["100px", null, null, null, "140px"]}
        objectFit="contain"
      />
    </VStack>
  );
}
