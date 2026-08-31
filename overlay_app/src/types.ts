export interface CharacterInfo {
  id: string;
  display_name: string;
  portrait_filename: string | null;
}

export interface PlayerInfo {
  id: number;
  display_name: string;
}

export interface BanRecord {
  character_id: string | null; // null = turno saltado (timeout_behavior="skip")
  banned_by_player_id: number;
  was_timeout: boolean;
}

// Espejo de build_match_state_payload() en backend/app/services/draft_service.py.
// match_id null significa "no hay partida elegida en el panel ahora mismo".
export interface MatchState {
  match_id: number | null;
  status?: "SETUP" | "BANNING" | "RANDOMIZING" | "REVEAL" | "DONE";
  player_a?: PlayerInfo;
  player_b?: PlayerInfo;
  tournament_name?: string;
  bans_per_player?: number;
  banned_character_ids?: string[];
  bans?: BanRecord[];
  current_turn_player_id?: number | null;
  results?: Record<string, string> | null;
  turn_deadline_ms?: number | null;
}

// Espejo de GET /api/broadcast-settings.
export interface BroadcastSettings {
  tournament_label: string | null;
  logo_choice: "tdf" | "torneo";
  logo_url: string | null;
}

// Espejo del evento Socket.IO "ban_candidate_preview" (checkpoint HUD-4).
// null significa que no hay nada seleccionado ahora mismo en el panel.
export interface CandidatePreview {
  character_id: string | null;
  player_id: number | null;
}
