import { Box, Text, VStack } from "@devup-ui/react";
import Image from "next/image";

interface HeaderProps {
  title: string;
  subTitle: string;
  image: string;
  color: string;
}

const IMAGE_SIZES: Record<string, { w: number; h: number }> = {
  safe: { w: 360, h: 360 },
  caution: { w: 162, h: 136 },
  danger: { w: 210, h: 164 },
  analyze: { w: 304, h: 304 },
  dead: { w: 160, h: 152 },
};

export function Header({ title, subTitle, image, color }: HeaderProps) {
  const size = IMAGE_SIZES[image] || { w: 1, h: 1 };

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
      <Box
        position="relative"
        w={["100px", null, null, null, "140px"]}
        style={{ aspectRatio: `${size.w} / ${size.h}` }}
        flexShrink={0}
      >
        <Image
          src={`/images/${image}.png`}
          alt=""
          fill
          style={{ objectFit: "contain" }}
          sizes="(max-width: 768px) 100px, 140px"
          priority
        />
      </Box>
    </VStack>
  );
}
