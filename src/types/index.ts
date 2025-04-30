export interface Reply {
  italian: string;
  english: string;
}

export interface TranscriptData {
  id: string;
  italian: string;
  english: string;
  replies: Reply[];
}