"use client";

import { AnalysisView } from "@/ui/AnalysisView";
import { Text, Flex } from "@devup-ui/react";
import { useState } from "react";
import type { StepStatus } from "@/ui/AnalysisView";

export default function AnalysisDebugPage() {
  const [steps, setSteps] = useState<{
    step1: StepStatus;
    step2: StepStatus;
    step3: StepStatus;
  }>({
    step1: "completed",
    step2: "in_progress",
    step3: "pending",
  });

  return (
    <div style={{ position: "relative", minHeight: "100vh", width: "100%" }}>
      {/* 상태 제어용 도구 (Floating 처리하여 실제 레이아웃 방해 최소화) */}
      <Flex
        gap="10px"
        p="12px"
        border="1px solid $gray"
        borderRadius="12px"
        bg="rgba(255, 255, 255, 0.8)"
        position="fixed"
        top="20px"
        right="20px"
        zIndex={9999}
        boxShadow="0 8px 32px rgba(0,0,0,0.12)"
        style={{ backdropFilter: "blur(8px)" }}
        alignItems="center"
      >
        <Text fontWeight="700" fontSize="14px" color="$black">
          DEBUG UI
        </Text>
        <div
          style={{
            width: "1px",
            height: "16px",
            backgroundColor: "#E2E8F0",
            margin: "0 4px",
          }}
        />
        <Flex
          as="button"
          onClick={() =>
            setSteps({ step1: "pending", step2: "pending", step3: "pending" })
          }
          px="12px"
          py="6px"
          borderRadius="6px"
          border="1px solid $gray"
          bg="$white"
          cursor="pointer"
          _hover={{ bg: "$background" }}
        >
          <Text fontSize="12px" fontWeight="600">
            초기
          </Text>
        </Flex>
        <Flex
          as="button"
          onClick={() =>
            setSteps({
              step1: "completed",
              step2: "in_progress",
              step3: "pending",
            })
          }
          px="12px"
          py="6px"
          borderRadius="6px"
          border="1px solid $gray"
          bg="$white"
          cursor="pointer"
          _hover={{ bg: "$background" }}
        >
          <Text fontSize="12px" fontWeight="600">
            진행중
          </Text>
        </Flex>
        <Flex
          as="button"
          onClick={() =>
            setSteps({
              step1: "completed",
              step2: "completed",
              step3: "completed",
            })
          }
          px="12px"
          py="6px"
          borderRadius="6px"
          border="1px solid $gray"
          bg="$white"
          cursor="pointer"
          _hover={{ bg: "$background" }}
        >
          <Text fontSize="12px" fontWeight="600">
            완료
          </Text>
        </Flex>
      </Flex>

      {/* 실제 서비스와 1:1 동일한 렌더링 환경 */}
      <AnalysisView {...steps} />
    </div>
  );
}
