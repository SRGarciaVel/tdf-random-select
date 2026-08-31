import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import type {
  BanRecord,
  BroadcastSettings,
  CharacterInfo,
  MatchState,
  PlayerInfo,
} from "./types";
import "./DraftOverlay.css";

interface DraftOverlayProps {
  matchState: MatchState;
  roster: CharacterInfo[];
  broadcastSettings: BroadcastSettings | null;
}

type RosterMap = Record<string, CharacterInfo>;

function portraitUrl(characterId: string): string {
  return `/portraits/${characterId}.webp`;
}

function statusMessage(matchState: MatchState): string {
  const { status, player_a, player_b, current_turn_player_id } = matchState;
  if (status === "SETUP") return "Listo para banear";
  if (status === "BANNING") {
    const name =
      current_turn_player_id === player_a?.id
        ? player_a?.display_name
        : player_b?.display_name;
    return `Turno de banear: ${name ?? ""}`;
  }
  if (status === "RANDOMIZING") return "Randomizando...";
  if (status === "REVEAL" || status === "DONE") return "Reveal";
  return "";
}

// Mismo tajo diagonal de la Fase 3, reutilizado dentro de los slots chicos del HUD.
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

function useCountdown(deadlineMs: number | null): number | null {
  const [remaining, setRemaining] = useState<number | null>(null);

  useEffect(() => {
    if (deadlineMs == null) {
      setRemaining(null);
      return;
    }
    const tick = () => {
      setRemaining(Math.max(0, Math.ceil((deadlineMs - Date.now()) / 1000)));
    };
    tick();
    const interval = setInterval(tick, 250);
    return () => clearInterval(interval);
  }, [deadlineMs]);

  return remaining;
}

function BanSlot({
  ban,
  roster,
  isActive,
  deadlineMs,
}: {
  ban: BanRecord | undefined;
  roster: RosterMap;
  isActive: boolean;
  deadlineMs: number | null;
}) {
  const remaining = useCountdown(isActive ? deadlineMs : null);
  const character = ban?.character_id ? roster[ban.character_id] : null;
  const wasSkipped = ban !== undefined && ban.character_id === null;
  const isFilled = character != null || wasSkipped;

  return (
    <motion.div
      key={isFilled ? "filled" : "empty"}
      className={`ban-slot${isFilled ? " filled" : " empty"}${isActive ? " active" : ""}`}
      data-testid={character ? `ban-slot-${character.id}` : undefined}
      initial={
        character ? { scale: 1, filter: "grayscale(0)", opacity: 1 } : false
      }
      animate={
        character
          ? { scale: [1, 1.08, 1], filter: "grayscale(1)", opacity: 0.55 }
          : {}
      }
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {character && (
        <>
          <img src={portraitUrl(character.id)} alt={character.display_name} />
          <BanSlash />
        </>
      )}
      {wasSkipped && (
        <div className="skipped-marker" data-testid="skipped-marker">
          —
        </div>
      )}
      {ban?.was_timeout && (
        <div
          className="timeout-icon"
          data-testid="timeout-icon"
          title="Se agotó el tiempo"
        >
          ⏱
        </div>
      )}
      {isActive && <div className="active-glow" />}
      {isActive && remaining !== null && (
        <div className="countdown" data-testid="countdown">
          {remaining}
        </div>
      )}
    </motion.div>
  );
}

function ResultCard({
  player,
  characterId,
  side,
}: {
  player: PlayerInfo;
  characterId: string;
  side: "left" | "right";
}) {
  return (
    <motion.div
      className="result-card"
      data-testid={`result-${side}`}
      initial={{ opacity: 0, scale: 0.6, x: side === "left" ? -40 : 40 }}
      animate={{ opacity: 1, scale: 1, x: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 20 }}
    >
      <img src={portraitUrl(characterId)} alt={characterId} />
      <span className="result-player-name">{player.display_name}</span>
    </motion.div>
  );
}

function PlayerSide({
  side,
  player,
  bans,
  bansPerPlayer,
  roster,
  isActive,
  deadlineMs,
  showResult,
  resultCharacterId,
}: {
  side: "left" | "right";
  player: PlayerInfo;
  bans: BanRecord[];
  bansPerPlayer: number;
  roster: RosterMap;
  isActive: boolean;
  deadlineMs: number | null;
  showResult: boolean;
  resultCharacterId: string | null;
}) {
  const slotIndices = Array.from({ length: bansPerPlayer }, (_, i) => i);
  // El primer baneo de cada jugador ocupa el slot mas cercano al centro
  // (indice 0) - del lado izquierdo eso significa dibujar los indices al
  // reves (el mas alto pegado al nombre, el 0 pegado al centro).
  const orderedIndices =
    side === "left" ? [...slotIndices].reverse() : slotIndices;

  const nameLabel = (
    <div className="player-name-label">{player.display_name}</div>
  );

  const slotsRow = (
    <div className="ban-slots">
      {orderedIndices.map((index) => (
        <BanSlot
          key={index}
          ban={bans[index]}
          roster={roster}
          isActive={isActive && index === bans.length}
          deadlineMs={deadlineMs}
        />
      ))}
    </div>
  );

  const resultArea = showResult && resultCharacterId && (
    <ResultCard player={player} characterId={resultCharacterId} side={side} />
  );

  return (
    <div className={`player-side player-side-${side}`}>
      {side === "left" && nameLabel}
      {showResult ? resultArea : slotsRow}
      {side === "right" && nameLabel}
    </div>
  );
}

function CenterPanel({
  broadcastSettings,
  matchState,
}: {
  broadcastSettings: BroadcastSettings | null;
  matchState: MatchState;
}) {
  const label =
    broadcastSettings?.tournament_label?.trim() ||
    matchState.tournament_name ||
    "";

  return (
    <div className="center-panel">
      {broadcastSettings?.logo_url && (
        <img
          className="center-logo"
          src={broadcastSettings.logo_url}
          alt=""
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
        />
      )}
      {label && <div className="center-label">{label}</div>}
      <div className="center-status">{statusMessage(matchState)}</div>
    </div>
  );
}

export default function DraftOverlay({
  matchState,
  roster,
  broadcastSettings,
}: DraftOverlayProps) {
  if (matchState.match_id === null) {
    return (
      <div className="overlay-root idle">
        <p>Esperando partida...</p>
      </div>
    );
  }

  const rosterMap: RosterMap = Object.fromEntries(
    roster.map((entry) => [entry.id, entry]),
  );
  const bansPerPlayer = matchState.bans_per_player ?? 0;
  const allBans = matchState.bans ?? [];
  const showResults =
    matchState.status === "REVEAL" || matchState.status === "DONE";
  const results = matchState.results ?? null;

  return (
    <div className="hud-bar">
      {matchState.player_a && (
        <PlayerSide
          side="left"
          player={matchState.player_a}
          bans={allBans.filter(
            (ban) => ban.banned_by_player_id === matchState.player_a?.id,
          )}
          bansPerPlayer={bansPerPlayer}
          roster={rosterMap}
          isActive={
            matchState.status === "BANNING" &&
            matchState.current_turn_player_id === matchState.player_a.id
          }
          deadlineMs={matchState.turn_deadline_ms ?? null}
          showResult={showResults}
          resultCharacterId={results?.[String(matchState.player_a.id)] ?? null}
        />
      )}

      <CenterPanel
        broadcastSettings={broadcastSettings}
        matchState={matchState}
      />

      {matchState.player_b && (
        <PlayerSide
          side="right"
          player={matchState.player_b}
          bans={allBans.filter(
            (ban) => ban.banned_by_player_id === matchState.player_b?.id,
          )}
          bansPerPlayer={bansPerPlayer}
          roster={rosterMap}
          isActive={
            matchState.status === "BANNING" &&
            matchState.current_turn_player_id === matchState.player_b.id
          }
          deadlineMs={matchState.turn_deadline_ms ?? null}
          showResult={showResults}
          resultCharacterId={results?.[String(matchState.player_b.id)] ?? null}
        />
      )}
    </div>
  );
}
