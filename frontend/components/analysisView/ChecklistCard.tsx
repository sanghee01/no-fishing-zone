"use client";

import { VStack } from "@devup-ui/react";
import type { ReactNode } from "react";

interface ChecklistCardProps {
  children: ReactNode;
}

export function ChecklistCard({ children }: ChecklistCardProps) {
  return (
    <VStack
      bg="#FFFFFF"
      border="1px solid #F1F5F9"
      borderRadius="24px"
      boxShadow="0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05)"
      gap="20px"
      w="100%"
      maxW="640px"
      px={["24px", null, null, null, "48px"]}
      py={["24px", null, null, null, "40px"]}
    >
      {children}
    </VStack>
  );
}
