import { useEffect, useState } from "react";
import DraftOverlay from "./DraftOverlay";
import socketConnection from "./socketConnection";
import type { CharacterInfo, MatchState } from "./types";

function App() {
  const [roster, setRoster] = useState<CharacterInfo[]>([]);
  const [matchState, setMatchState] = useState<MatchState>({ match_id: null });

  useEffect(() => {
    fetch("/api/roster")
      .then((res) => res.json())
      .then((data: CharacterInfo[]) => setRoster(data))
      .catch((err) => console.error("No se pudo cargar el roster:", err));

    const socket = socketConnection.get();
    socket.on("match_state_update", (payload: MatchState) => {
      setMatchState(payload);
    });

    return () => {
      socket.off("match_state_update");
    };
  }, []);

  return <DraftOverlay matchState={matchState} roster={roster} />;
}

export default App;
