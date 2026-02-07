export type UrlReputationStatus = "SAFE" | "WARNING" | "BLOCK" | "DEAD";

export interface UrlReputationResponse {
  url: string;
  description: string | null;
  score: number;
  status: UrlReputationStatus;
}

export type StepStatus = "pending" | "in_progress" | "completed";
