import { useEffect, useState } from "react";
import DraftOverlay from "./DraftOverlay";
import socketConnection from "./socketConnection";
import type {
  BroadcastSettings,
  CandidatePreview,
  CharacterInfo,
  CharacterStatsUpdate,
  MatchState,
} from "./types";

function App() {
  const [roster, setRoster] = useState<CharacterInfo[]>([]);
  const [broadcastSettings, setBroadcastSettings] =
    useState<BroadcastSettings | null>(null);
  const [matchState, setMatchState] = useState<MatchState>({ match_id: null });
  const [candidatePreview, setCandidatePreview] =
    useState<CandidatePreview | null>(null);
  const [characterStats, setCharacterStats] =
    useState<CharacterStatsUpdate | null>(null);

  useEffect(() => {
    fetch("/api/roster")
      .then((res) => res.json())
      .then((data: CharacterInfo[]) => setRoster(data))
      .catch((err) => console.error("No se pudo cargar el roster:", err));

    fetch("/api/broadcast-settings")
      .then((res) => res.json())
      .then((data: BroadcastSettings) => setBroadcastSettings(data))
      .catch((err) =>
        console.error("No se pudo cargar broadcast-settings:", err),
      );

    const socket = socketConnection.get();
    socket.on("match_state_update", (payload: MatchState) => {
      setMatchState(payload);
      // Cualquier accion real confirmada (baneo, randomize, reveal, etc.)
      // deja obsoleto cualquier preview de seleccion o estadistica que
      // hubiera quedado colgada - se limpia siempre, no solo cuando
      // corresponde al personaje recien baneado. El panel ya manda su
      // propio "visible:false" explicito antes de esto (checkpoint
      // HUD-10), esto es una red de seguridad extra por si ese evento
      // se pierde en el viaje.
      setCandidatePreview(null);
      setCharacterStats(null);
    });
    socket.on("ban_candidate_preview", (payload: CandidatePreview) => {
      setCandidatePreview(payload.character_id ? payload : null);
    });
    socket.on("character_stats_update", (payload: CharacterStatsUpdate) => {
      setCharacterStats(payload.visible ? payload : null);
    });

    return () => {
      socket.off("match_state_update");
      socket.off("ban_candidate_preview");
      socket.off("character_stats_update");
    };
  }, []);

  return (
    <DraftOverlay
      matchState={matchState}
      roster={roster}
      broadcastSettings={broadcastSettings}
      candidatePreview={candidatePreview}
      characterStats={characterStats}
    />
  );
}

export default App;
