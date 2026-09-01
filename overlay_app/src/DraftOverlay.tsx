import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import type {
  BanRecord,
  BroadcastSettings,
  CandidatePreview,
  CharacterInfo,
  MatchState,
  PlayerInfo,
} from "./types";
import "./DraftOverlay.css";

interface DraftOverlayProps {
  matchState: MatchState;
  roster: CharacterInfo[];
  broadcastSettings: BroadcastSettings | null;
  candidatePreview?: CandidatePreview | null;
}

type RosterMap = Record<string, CharacterInfo>;

function portraitUrl(characterId: string): string {
  return `/portraits/${characterId}.webp`;
}

// Panel dramatico full-height: se nota la calidad a ese tamaño, por eso
// usa la carpeta grande en PNG en vez de los WebP chicos de los slots
// (checkpoint HUD-5, corregido a pedido de Seba tras ver el HUD real).
function portraitUrlLarge(characterId: string): string {
  return `/portraits-large/${characterId}.png`;
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

// Placa con corte diagonal (identidad visual de TDF, mismo lenguaje que
// el hud-frame de tdf-edeportes) - compartida entre el nombre del
// jugador en la franja compacta y el nombre del personaje/jugador en el
// panel dramatico (checkpoint HUD-7, ver ROADMAP.md).
function DiagonalPlate({
  side,
  text,
  size,
}: {
  side: "left" | "right";
  text: string;
  size: "small" | "large";
}) {
  return (
    <div className={`diagonal-plate diagonal-plate-${side}`}>
      <span className={`diagonal-plate-text diagonal-plate-text-${size}`}>
        {text}
      </span>
    </div>
  );
}

function FilledBanCard({ ban, roster }: { ban: BanRecord; roster: RosterMap }) {
  const character = ban.character_id ? roster[ban.character_id] : null;

  return (
    <motion.div
      className="ban-card filled"
      data-testid={character ? `ban-card-${character.id}` : undefined}
      initial={{ scale: 1, opacity: 1 }}
      animate={{ scale: [1, 1.08, 1], opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <div className="ban-card-inner">
        {character ? (
          <>
            <motion.img
              layoutId={`char-${character.id}`}
              src={portraitUrl(character.id)}
              alt={character.display_name}
              initial={{ filter: "grayscale(0)" }}
              animate={{ filter: "grayscale(1)" }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
            <BanSlash />
          </>
        ) : (
          <div className="skipped-marker" data-testid="skipped-marker">
            —
          </div>
        )}
        {ban.was_timeout && (
          <div
            className="timeout-icon"
            data-testid="timeout-icon"
            title="Se agotó el tiempo"
          >
            ⏱
          </div>
        )}
      </div>
    </motion.div>
  );
}

function EmptyBanCard({
  index,
  side,
  isActive,
  deadlineMs,
}: {
  index: number;
  side: "left" | "right";
  isActive: boolean;
  deadlineMs: number | null;
}) {
  const remaining = useCountdown(isActive ? deadlineMs : null);
  // index 0 = la proxima a banearse, pegada a la fila de baneadas
  // (mas cerca del centro). Las siguientes se asoman detras, hacia el
  // nombre - mismo criterio que antes, pero ahora solo aplica a las
  // que TODAVIA no se banearon (las baneadas se van a la fila visible).
  const peekOffsetPx = index * 22;
  const style: React.CSSProperties = {
    zIndex: 100 - index,
    height: `${100 - index * 6}%`,
    [side === "left" ? "right" : "left"]: `${peekOffsetPx}px`,
  };

  return (
    <div className={`ban-card empty${isActive ? " active" : ""}`} style={style}>
      {isActive && <div className="active-glow" />}
      {isActive && remaining !== null && (
        <div className="countdown" data-testid="countdown">
          {remaining}
        </div>
      )}
    </div>
  );
}

function BanCardStack({
  side,
  bans,
  bansPerPlayer,
  roster,
  isActive,
  deadlineMs,
}: {
  side: "left" | "right";
  bans: BanRecord[];
  bansPerPlayer: number;
  roster: RosterMap;
  isActive: boolean;
  deadlineMs: number | null;
}) {
  const remainingCount = Math.max(0, bansPerPlayer - bans.length);
  const emptyIndices = Array.from({ length: remainingCount }, (_, i) => i);
  // El primer baneo de cada jugador queda mas cerca del centro - del lado
  // izquierdo eso significa dibujar la fila al reves (el mas antiguo
  // pegado al centro, no al nombre).
  const orderedFilledBans = side === "left" ? [...bans].reverse() : bans;

  const filledRow = bans.length > 0 && (
    <div className={`ban-row ban-row-${side}`}>
      {orderedFilledBans.map((ban, i) => (
        <FilledBanCard
          key={ban.character_id ?? `skip-${i}`}
          ban={ban}
          roster={roster}
        />
      ))}
    </div>
  );

  const emptyStack = remainingCount > 0 && (
    <div className={`ban-empty-stack ban-empty-stack-${side}`}>
      {emptyIndices.map((index) => (
        <EmptyBanCard
          key={index}
          index={index}
          side={side}
          isActive={isActive && index === 0}
          deadlineMs={deadlineMs}
        />
      ))}
    </div>
  );

  return (
    <motion.div
      className={`ban-card-stack ban-card-stack-${side}`}
      data-testid={`ban-card-stack-${side}`}
      // El mazo entero "nace" del panel central al arrancar el baneo -
      // arranca corrido hacia el centro (un ancho propio de distancia) y
      // se acomoda en su posicion final. Solo pasa una vez, al montar
      // (cuando status pasa de SETUP a BANNING, ver PlayerSide).
      initial={{ x: side === "left" ? "120%" : "-120%", opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 24 }}
    >
      {side === "left" ? (
        <>
          {emptyStack}
          {filledRow}
        </>
      ) : (
        <>
          {filledRow}
          {emptyStack}
        </>
      )}
    </motion.div>
  );
}

function DramaticCharacterPanel({
  character,
  playerName,
  side,
  testId,
}: {
  character: CharacterInfo;
  playerName: string;
  side: "left" | "right";
  testId: string;
}) {
  return (
    <motion.div
      key={character.id}
      className={`dramatic-panel dramatic-panel-${side}`}
      data-testid={testId}
      initial={{ x: side === "left" ? "-100%" : "100%", opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: side === "left" ? "-100%" : "100%", opacity: 0 }}
      transition={{ type: "spring", stiffness: 220, damping: 28 }}
    >
      <motion.img
        layoutId={`char-${character.id}`}
        className="dramatic-panel-img"
        src={portraitUrlLarge(character.id)}
        alt={character.display_name}
      />
      <div className="dramatic-panel-plates">
        <DiagonalPlate side={side} text={character.display_name} size="large" />
        <DiagonalPlate side={side} text={playerName} size="small" />
      </div>
    </motion.div>
  );
}

function PlayerSide({
  side,
  player,
  status,
  bans,
  bansPerPlayer,
  roster,
  isActive,
  deadlineMs,
  showsInDramaticPanel,
}: {
  side: "left" | "right";
  player: PlayerInfo;
  status: MatchState["status"];
  bans: BanRecord[];
  bansPerPlayer: number;
  roster: RosterMap;
  isActive: boolean;
  deadlineMs: number | null;
  showsInDramaticPanel: boolean;
}) {
  // El mazo recien "nace" (se reparte desde el centro) cuando arranca el
  // baneo - antes de eso (SETUP) no hay nada que mostrar todavia.
  const showStack = status !== "SETUP";

  return (
    <div className={`player-side player-side-${side}`}>
      {/* Si el panel dramatico ya esta mostrando este nombre (apilado
       * bajo el personaje), no lo repetimos aca - se veia como un
       * nombre duplicado (checkpoint HUD-7.2, a pedido de Seba tras ver
       * el HUD real). */}
      {!showsInDramaticPanel && (
        <DiagonalPlate side={side} text={player.display_name} size="small" />
      )}
      {showStack && (
        <BanCardStack
          side={side}
          bans={bans}
          bansPerPlayer={bansPerPlayer}
          roster={roster}
          isActive={isActive}
          deadlineMs={deadlineMs}
        />
      )}
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
      <div className="center-panel-brand">
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
        {label && <span className="center-label">{label}</span>}
      </div>
      <div className="center-vs">VS</div>
      <div className="center-panel-footer">
        <div className="center-divider" />
        <div className="center-status">{statusMessage(matchState)}</div>
      </div>
    </div>
  );
}

export default function DraftOverlay({
  matchState,
  roster,
  broadcastSettings,
  candidatePreview = null,
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

  const dramaticCharacterFor = (
    playerId: number | undefined,
  ): CharacterInfo | null => {
    if (playerId === undefined) return null;
    if (showResults) {
      const resultId = results?.[String(playerId)];
      return resultId ? (rosterMap[resultId] ?? null) : null;
    }
    if (
      candidatePreview?.character_id &&
      candidatePreview.player_id === playerId
    ) {
      return rosterMap[candidatePreview.character_id] ?? null;
    }
    return null;
  };

  const accentColor = broadcastSettings?.accent_color || "#c400ff";
  const panelBackgroundColor =
    broadcastSettings?.panel_background_color || "rgba(10, 5, 15, 0.35)";

  const leftDramaticCharacter = matchState.player_a
    ? dramaticCharacterFor(matchState.player_a.id)
    : null;
  const rightDramaticCharacter = matchState.player_b
    ? dramaticCharacterFor(matchState.player_b.id)
    : null;

  return (
    <div
      className="hud-root"
      style={
        {
          "--hud-accent-color": accentColor,
          "--hud-panel-bg-color": panelBackgroundColor,
        } as React.CSSProperties
      }
    >
      <AnimatePresence>
        {leftDramaticCharacter && (
          <DramaticCharacterPanel
            character={leftDramaticCharacter}
            playerName={matchState.player_a?.display_name ?? ""}
            side="left"
            testId="dramatic-left"
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {rightDramaticCharacter && (
          <DramaticCharacterPanel
            character={rightDramaticCharacter}
            playerName={matchState.player_b?.display_name ?? ""}
            side="right"
            testId="dramatic-right"
          />
        )}
      </AnimatePresence>

      <div className="hud-bottom-bar">
        {matchState.player_a && (
          <PlayerSide
            side="left"
            player={matchState.player_a}
            status={matchState.status}
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
            showsInDramaticPanel={leftDramaticCharacter !== null}
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
            status={matchState.status}
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
            showsInDramaticPanel={rightDramaticCharacter !== null}
          />
        )}
      </div>
    </div>
  );
}
