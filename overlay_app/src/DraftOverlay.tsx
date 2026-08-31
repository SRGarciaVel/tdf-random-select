import { motion } from "framer-motion";
import type { CharacterInfo, MatchState } from "./types";
import "./DraftOverlay.css";

interface DraftOverlayProps {
  matchState: MatchState;
  roster: CharacterInfo[];
}

function portraitUrl(characterId: string): string {
  return `/portraits/${characterId}.webp`;
}

function playerName(
  matchState: MatchState,
  playerId: number | null | undefined,
): string {
  if (playerId == null) return "";
  if (matchState.player_a?.id === playerId)
    return matchState.player_a.display_name;
  if (matchState.player_b?.id === playerId)
    return matchState.player_b.display_name;
  return "";
}

function StatusBanner({ matchState }: { matchState: MatchState }) {
  const { status, player_a, player_b, current_turn_player_id } = matchState;

  if (status === "SETUP") {
    return (
      <p className="status-banner">
        {player_a?.display_name} vs {player_b?.display_name} - listo para banear
      </p>
    );
  }
  if (status === "BANNING") {
    return (
      <p className="status-banner">
        Turno de banear: {playerName(matchState, current_turn_player_id)}
      </p>
    );
  }
  if (status === "RANDOMIZING") {
    return <p className="status-banner">Randomizando...</p>;
  }
  if (status === "REVEAL" || status === "DONE") {
    return <p className="status-banner">Reveal</p>;
  }
  return null;
}

// Tajo diagonal que cruza el retrato al confirmarse el baneo. scaleX anima
// de 0 a 1 (el corte "avanza"), luego se desvanece dejando el retrato
// baneado en su estado final (gris, ver .character-card.banned en CSS).
function BanSlash() {
  return (
    <motion.div
      className="ban-slash"
      style={{ rotate: -20 }}
      initial={{ scaleX: 0, opacity: 1 }}
      animate={{ scaleX: 1, opacity: [1, 1, 0] }}
      transition={{ duration: 0.6, times: [0, 0.4, 1], ease: "easeOut" }}
    />
  );
}

function CharacterCard({
  character,
  isBanned,
}: {
  character: CharacterInfo;
  isBanned: boolean;
}) {
  return (
    <motion.div
      // Cambiar la key fuerza un remount cuando isBanned pasa de false a
      // true - garantiza que la animacion de baneo corre UNA vez en ese
      // momento, y nunca se repite en renders posteriores donde el
      // personaje ya sigue baneado (otros baneos del mismo match).
      key={isBanned ? "banned" : "active"}
      className={`character-card${isBanned ? " banned" : ""}`}
      data-testid={`character-${character.id}`}
      initial={
        isBanned ? { scale: 1, filter: "grayscale(0)", opacity: 1 } : false
      }
      animate={
        isBanned
          ? { scale: [1, 1.08, 1], filter: "grayscale(1)", opacity: 0.35 }
          : {}
      }
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <img src={portraitUrl(character.id)} alt={character.display_name} />
      <span className="character-name">{character.display_name}</span>
      {isBanned && <BanSlash />}
    </motion.div>
  );
}

function ResultCard({
  playerName,
  characterId,
  testId,
  delay,
}: {
  playerName: string;
  characterId: string;
  testId: string;
  delay: number;
}) {
  return (
    <motion.div
      className="result-card"
      data-testid={testId}
      initial={{ opacity: 0, scale: 0.6, y: 30 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 20, delay }}
    >
      <span className="result-player-name">{playerName}</span>
      <img src={portraitUrl(characterId)} alt={characterId} />
    </motion.div>
  );
}

function ResultsPanel({ matchState }: { matchState: MatchState }) {
  if (!matchState.results) return null;
  const { player_a, player_b, results } = matchState;

  return (
    <div className="results-panel">
      {player_a && results[String(player_a.id)] && (
        <ResultCard
          playerName={player_a.display_name}
          characterId={results[String(player_a.id)]}
          testId="result-player-a"
          delay={0}
        />
      )}
      {player_b && results[String(player_b.id)] && (
        <ResultCard
          playerName={player_b.display_name}
          characterId={results[String(player_b.id)]}
          testId="result-player-b"
          delay={0.15}
        />
      )}
    </div>
  );
}

export default function DraftOverlay({
  matchState,
  roster,
}: DraftOverlayProps) {
  if (matchState.match_id === null) {
    return (
      <div className="overlay-root idle">
        <p>Esperando partida...</p>
      </div>
    );
  }

  const bannedIds = new Set(matchState.banned_character_ids ?? []);
  const showResults =
    matchState.status === "REVEAL" || matchState.status === "DONE";

  return (
    <div className="overlay-root">
      <StatusBanner matchState={matchState} />
      {showResults ? (
        <ResultsPanel matchState={matchState} />
      ) : (
        <div className="character-grid">
          {roster.map((character) => (
            <CharacterCard
              key={character.id}
              character={character}
              isBanned={bannedIds.has(character.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
