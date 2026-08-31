import { useEffect, useState } from "react";
import DraftOverlay from "./DraftOverlay";
import socketConnection from "./socketConnection";
import type {
  BroadcastSettings,
  CandidatePreview,
  CharacterInfo,
  MatchState,
} from "./types";

function App() {
  const [roster, setRoster] = useState<CharacterInfo[]>([]);
  const [broadcastSettings, setBroadcastSettings] =
    useState<BroadcastSettings | null>(null);
  const [matchState, setMatchState] = useState<MatchState>({ match_id: null });
  const [candidatePreview, setCandidatePreview] =
    useState<CandidatePreview | null>(null);

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
      // deja obsoleto cualquier preview de seleccion que hubiera quedado
      // colgado - se limpia siempre, no solo cuando corresponde al
      // personaje recien baneado.
      setCandidatePreview(null);
    });
    socket.on("ban_candidate_preview", (payload: CandidatePreview) => {
      setCandidatePreview(payload.character_id ? payload : null);
    });

    return () => {
      socket.off("match_state_update");
      socket.off("ban_candidate_preview");
    };
  }, []);

  return (
    <DraftOverlay
      matchState={matchState}
      roster={roster}
      broadcastSettings={broadcastSettings}
      candidatePreview={candidatePreview}
    />
  );
}

export default App;
