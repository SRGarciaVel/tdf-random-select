export interface CharacterInfo {
  id: string;
  display_name: string;
  portrait_filename: string | null;
}

export interface PlayerInfo {
  id: number;
  display_name: string;
}

// Espejo de build_match_state_payload() en backend/app/services/draft_service.py.
// match_id null significa "no hay partida elegida en el panel ahora mismo".
export interface MatchState {
  match_id: number | null;
  status?: "SETUP" | "BANNING" | "RANDOMIZING" | "REVEAL" | "DONE";
  player_a?: PlayerInfo;
  player_b?: PlayerInfo;
  banned_character_ids?: string[];
  current_turn_player_id?: number | null;
  results?: Record<string, string> | null;
}
