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

function ResultsPanel({ matchState }: { matchState: MatchState }) {
  if (!matchState.results) return null;
  const { player_a, player_b, results } = matchState;

  return (
    <div className="results-panel">
      {player_a && results[String(player_a.id)] && (
        <div className="result-card" data-testid="result-player-a">
          <span className="result-player-name">{player_a.display_name}</span>
          <img
            src={portraitUrl(results[String(player_a.id)])}
            alt={results[String(player_a.id)]}
          />
        </div>
      )}
      {player_b && results[String(player_b.id)] && (
        <div className="result-card" data-testid="result-player-b">
          <span className="result-player-name">{player_b.display_name}</span>
          <img
            src={portraitUrl(results[String(player_b.id)])}
            alt={results[String(player_b.id)]}
          />
        </div>
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
          {roster.map((character) => {
            const isBanned = bannedIds.has(character.id);
            return (
              <div
                key={character.id}
                className={`character-card${isBanned ? " banned" : ""}`}
                data-testid={`character-${character.id}`}
              >
                <img
                  src={portraitUrl(character.id)}
                  alt={character.display_name}
                />
                <span className="character-name">{character.display_name}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
