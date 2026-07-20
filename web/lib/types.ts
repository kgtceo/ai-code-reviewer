// Mirrors the backend Pydantic models (ai_code_reviewer.models).

export type Severity = "critical" | "high" | "medium" | "low";
export type Category = "bug" | "security" | "correctness" | "performance";

export interface Finding {
  file: string;
  line: number;
  severity: Severity;
  category: Category;
  issue: string;
  suggestion: string;
  snippet: string;
}

export interface Review {
  summary: string;
  findings: Finding[];
}

export interface ReviewResult {
  review: Review;
  files_reviewed: string[];
  changed_line_count: number;
}
