export interface Reply {
  original: string;
  english: string;
}

export interface TranscriptData {
  id: string;
  original: string;
  english: string;
  replies: Reply[];
  detected_language?: string; // Language code detected by the backend
}