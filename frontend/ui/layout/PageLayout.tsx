import { Box, Center, Flex, Text, VStack } from "@devup-ui/react";
import Image from "next/image";
import type { ReactNode } from "react";

interface PageLayoutProps {
  children: ReactNode;
  variant?: "default" | "danger" | "caution";
}

interface HeaderProps {
  children: ReactNode;
}

interface ContentProps {
  children: ReactNode;
}

/**
 * PageLayout - Compound Component 패턴
 * AnalysisView, DangerView, CautionView, SafeView에서 공통으로 사용
 */
export function PageLayoutRoot({ children }: PageLayoutProps) {
  return (
    <VStack bg="$background" minH="100vh" w="100%" alignItems="center">
      {children}
    </VStack>
  );
}

export function PageLayoutHeader({ children }: HeaderProps) {
  return (
    <Center w="100%" pt={["60px", null, null, null, "100px"]} pb="20px">
      {children}
    </Center>
  );
}

export function PageLayoutContent({ children }: ContentProps) {
  return (
    <VStack
      flex="1"
      w="100%"
      maxW="900px"
      px="24px"
      alignItems="center"
      gap={["40px", null, null, null, "60px"]}
      pb="100px"
    >
      {children}
    </VStack>
  );
}

export function PageLayoutFooter() {
  return (
    <Center
      bg="$white"
      borderTop="solid 1px"
      borderTopColor="$gray"
      w="100%"
      py={["16px", null, null, null, "64px"]}
    >
      <Flex alignItems="center" gap="8px">
        <Box
          position="relative"
          borderRadius="67px"
          aspectRatio="1"
          boxSize={["48px", null, null, null, "134px"]}
          overflow="hidden"
        >
          <Image
            src="/images/logo.png"
            alt="낚시금지구역 로고"
            fill
            priority
            style={{ objectFit: "cover" }}
          />
        </Box>
        <VStack>
          <Text
            color="$black"
            fontFamily="Inter"
            fontWeight="700"
            fontSize={["14px", null, null, null, "24px"]}
            textAlign="center"
            lineHeight="1.2"
          >
            낚시금지구역
          </Text>
          <Text
            color="$black"
            fontFamily="Inter"
            fontWeight="700"
            fontSize={["11px", null, null, null, "16px"]}
            textAlign="center"
            lineHeight="1.2"
          >
            no-fishing zone
          </Text>
        </VStack>
      </Flex>
    </Center>
  );
}

// Compound Component Export
export const PageLayout = Object.assign(PageLayoutRoot, {
  Header: PageLayoutHeader,
  Content: PageLayoutContent,
  Footer: PageLayoutFooter,
});
