"use client";

import { Flex, Text } from "@devup-ui/react";
import { Check, Circle, Loader2 } from "lucide-react";
import { css, keyframes } from "@devup-ui/react";

const spin = keyframes({
  "0%": { transform: "rotate(0deg)" },
  "100%": { transform: "rotate(360deg)" },
});

export type StepStatus = "pending" | "in_progress" | "completed";

export interface ChecklistItemProps {
  label: string;
  status: StepStatus;
}

/**
 * 체크리스트 아이템 컴포넌트
 * - completed: 체크 아이콘 (파란색)
 * - in_progress: 회전하는 로딩 아이콘
 * - pending: 빈 원 아이콘 (회색)
 */
export function ChecklistItem({ label, status }: ChecklistItemProps) {
  const statusText = {
    pending: "대기",
    in_progress: "진행 중",
    completed: "완료",
  }[status];

  const iconContainerStyle = css({
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxSize: "24px",
    borderRadius: "50%",
    bg: status === "completed" ? "#003366" : "transparent",
    border: status === "completed" ? "none" : "2px solid",
    borderColor: status === "pending" ? "#CBD5E1" : "#003366",
  });

  const spinnerStyle = css({
    animation: `${spin} 1s linear infinite`,
  });

  return (
    <Flex alignItems="center" justifyContent="space-between" w="100%" py="8px">
      <Flex alignItems="center" gap="14px">
        <span className={iconContainerStyle}>
          {status === "completed" && (
            <Check size={14} color="white" strokeWidth={3} />
          )}
          {status === "in_progress" && (
            <Loader2
              size={16}
              color="var(--primary)"
              className={spinnerStyle}
            />
          )}
          {status === "pending" && (
            <Circle size={6} color="#CBD5E1" fill="#CBD5E1" />
          )}
        </span>
        <Text
          color={status === "pending" ? "#94A3B8" : "#1E293B"}
          fontSize="17px"
          fontWeight="500"
          letterSpacing="-0.01em"
        >
          {label}
        </Text>
      </Flex>
      <Text
        color={status === "pending" ? "#CBD5E1" : "#1E293B"}
        fontSize="15px"
        fontWeight="600"
      >
        {statusText}
      </Text>
    </Flex>
  );
}
