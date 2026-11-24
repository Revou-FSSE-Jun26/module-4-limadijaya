// API data transfer objects. They mirror the Flask responses in specs/design.md section 5.2.

export interface UserPublic {
  id: string;
  name: string;
  email: string;
}

export interface MemberRef {
  id: string;
  name: string;
}

export interface BoardSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Card {
  id: string;
  column_id: string;
  title: string;
  order: number;
  assignee_id: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CardMoveResult extends Card {
  rebalanced: boolean;
}

export interface MyTaskCard extends Card {
  board_id: string;
  board_name: string;
}

export interface Column {
  id: string;
  name: string;
  order: number;
  is_done: boolean;
}

export interface ColumnWithCards extends Column {
  cards: Card[];
}

export type BoardRole = "administrator" | "member";

export interface BoardDetail {
  id: string;
  name: string;
  role: BoardRole;
  members: MemberRef[];
  columns: ColumnWithCards[];
}

export interface Comment {
  id: string;
  card_id: string;
  content: string;
  author: MemberRef;
  created_at: string;
  updated_at: string;
}

export interface NotificationItem {
  id: string;
  type: "card_assigned" | "comment_added";
  message: string;
  board_id: string;
  card_id: string;
  actor: MemberRef;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPage {
  items: NotificationItem[];
  page: number;
  per_page: number;
  total: number;
  unread_count: number;
}

export interface Analytics {
  window: { start: string; end: string };
  cards_per_column: { column_id: string; name: string; card_count: number }[];
  completed_this_week: number;
  member_activity: { user_id: string; name: string; activity_count: number }[];
}

export interface SessionState {
  authenticated: boolean;
  expiresAt: string | null;
}

export interface LoginResult {
  user: UserPublic;
  expires_at: string;
}
