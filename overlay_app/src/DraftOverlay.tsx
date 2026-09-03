import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type {
  BanRecord,
  BroadcastSettings,
  CandidatePreview,
  CharacterInfo,
  CharacterStatsUpdate,
  MatchState,
  PlayerInfo,
} from "./types";
import "./DraftOverlay.css";

interface DraftOverlayProps {
  matchState: MatchState;
  roster: CharacterInfo[];
  broadcastSettings: BroadcastSettings | null;
  candidatePreview?: CandidatePreview | null;
  characterStats?: CharacterStatsUpdate | null;
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

function FilledBanCard({
  ban,
  roster,
  characterStats,
}: {
  ban: BanRecord;
  roster: RosterMap;
  characterStats: CharacterStatsUpdate | null;
}) {
  const character = ban.character_id ? roster[ban.character_id] : null;

  // Esta carta se acaba de banear (recien montada) - el pulso dura 0.9s
  // y despues se apaga solo, simulando que la linea del perimetro "la
  // abraza" una vez al pasar (checkpoint HUD-9, ver ROADMAP.md).
  const [justBanned, setJustBanned] = useState(true);
  useEffect(() => {
    const timeout = setTimeout(() => setJustBanned(false), 900);
    return () => clearTimeout(timeout);
  }, []);

  // El staff activo a mano "Mostrar estadisticas" para ESTA carta
  // puntual (siempre el ultimo baneo confirmado) - checkpoint HUD-10.
  const showStats =
    characterStats !== null &&
    characterStats.player_id === ban.banned_by_player_id &&
    characterStats.character_id === ban.character_id;

  return (
    <motion.div
      className={`ban-card filled${justBanned ? " just-banned" : ""}`}
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
        <AnimatePresence>
          {showStats && character && (
            <motion.div
              className="ban-card-stats-wipe"
              data-testid={`ban-card-stats-${character.id}`}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              exit={{ scaleX: 0 }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
              style={{ transformOrigin: "left" }}
            >
              <motion.div
                className="ban-card-stats-content"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25, delay: 0.35 }}
              >
                <span className="ban-card-stats-name">
                  {character.display_name.toUpperCase()}
                </span>
                {characterStats.ever_played ? (
                  <span className="ban-card-stats-winrate">
                    <span className="ban-card-stats-winrate-label">WIN%</span>
                    <span className="ban-card-stats-winrate-value">
                      {((characterStats.win_rate ?? 0) * 100).toFixed(1)}%
                    </span>
                  </span>
                ) : (
                  <span className="ban-card-stats-never-played">
                    Nunca jugado
                  </span>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
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
  rowRef,
  characterStats,
}: {
  side: "left" | "right";
  bans: BanRecord[];
  bansPerPlayer: number;
  roster: RosterMap;
  isActive: boolean;
  deadlineMs: number | null;
  rowRef?: React.RefObject<HTMLDivElement | null>;
  characterStats: CharacterStatsUpdate | null;
}) {
  const remainingCount = Math.max(0, bansPerPlayer - bans.length);
  const emptyIndices = Array.from({ length: remainingCount }, (_, i) => i);
  // El primer baneo de cada jugador queda mas cerca del centro - del lado
  // izquierdo eso significa dibujar la fila al reves (el mas antiguo
  // pegado al centro, no al nombre).
  const orderedFilledBans = side === "left" ? [...bans].reverse() : bans;

  // rowRef mide la fila de baneadas real - PerimeterLight (checkpoint
  // HUD-9) la usa para trazar el contorno de la figura conectada, que
  // solo incluye lo YA baneado, no el mazo compacto de pendientes.
  const filledRow = bans.length > 0 && (
    <div className={`ban-row ban-row-${side}`} ref={rowRef}>
      {orderedFilledBans.map((ban, i) => (
        <FilledBanCard
          key={ban.character_id ?? `skip-${i}`}
          ban={ban}
          roster={roster}
          characterStats={characterStats}
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
  rowRef,
  characterStats,
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
  rowRef?: React.RefObject<HTMLDivElement | null>;
  characterStats: CharacterStatsUpdate | null;
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
          rowRef={rowRef}
          characterStats={characterStats}
        />
      )}
    </div>
  );
}

// Linea con estela que recorre el contorno completo (360°) de la figura
// conectada (mazo izquierdo + panel central + mazo derecho) - checkpoint
// HUD-9, a pedido de Seba. Mide posiciones REALES del DOM (no matematica
// pura) porque las cartas y el panel central tienen alturas distintas
// (85%/88%) y calcularlo a mano sin ver el render real es demasiado
// arriesgado - mejor que se ajuste sola a donde este todo de verdad,
// incluida la cantidad de cartas ya baneadas (crece con cada baneo).
export type PerimeterBox = {
  left: number;
  right: number;
  top: number;
  bottom: number;
};

function measureRelativeTo(
  el: HTMLElement,
  containerRect: DOMRect,
): PerimeterBox {
  const rect = el.getBoundingClientRect();
  return {
    left: rect.left - containerRect.left,
    right: rect.right - containerRect.left,
    top: rect.top - containerRect.top,
    bottom: rect.bottom - containerRect.top,
  };
}

// Conecta los bordes de arriba y de abajo de cada caja con una diagonal
// hacia la siguiente en vez de un escalon recto - da una silueta mas
// fluida para que viaje la luz, y funciona con 1, 2 o 3 cajas (por si
// todavia no hay cartas baneadas de un lado, o estamos en SETUP).
export function buildPerimeterPath(
  boxes: PerimeterBox[],
  skew: number,
): string {
  if (boxes.length === 0) return "";
  const first = boxes[0];
  const last = boxes[boxes.length - 1];

  const segments: string[] = [`M ${first.left} ${first.bottom}`];
  segments.push(`L ${first.left + skew} ${first.top}`);
  boxes.forEach((box, i) => {
    segments.push(`L ${box.right} ${box.top}`);
    if (i < boxes.length - 1) {
      const next = boxes[i + 1];
      segments.push(`L ${next.left + skew} ${next.top}`);
    }
  });
  segments.push(`L ${last.right - skew} ${last.bottom}`);
  for (let i = boxes.length - 1; i >= 0; i--) {
    const box = boxes[i];
    segments.push(`L ${box.left} ${box.bottom}`);
    if (i > 0) {
      const prev = boxes[i - 1];
      segments.push(`L ${prev.right - skew} ${prev.bottom}`);
    }
  }
  segments.push("Z");
  return segments.join(" ");
}

function PerimeterLight({
  containerRef,
  boxRefs,
  skewPx,
}: {
  containerRef: React.RefObject<HTMLElement | null>;
  boxRefs: React.RefObject<HTMLElement | null>[];
  skewPx: number;
}) {
  const [pathD, setPathD] = useState("");

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    function recompute() {
      const containerEl = containerRef.current;
      if (!containerEl) return;
      const containerRect = containerEl.getBoundingClientRect();
      const boxes = boxRefs
        .map((ref) => ref.current)
        .filter((el): el is HTMLElement => el !== null)
        .map((el) => measureRelativeTo(el, containerRect));
      setPathD(buildPerimeterPath(boxes, skewPx));
    }

    recompute();
    // jsdom (entorno de test) no implementa ResizeObserver - en
    // navegadores reales (y en OBS) siempre esta disponible.
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(recompute);
    observer.observe(container);
    boxRefs.forEach((ref) => {
      if (ref.current) observer.observe(ref.current);
    });
    window.addEventListener("resize", recompute);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", recompute);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  });

  if (!pathD) return null;

  return (
    <svg className="perimeter-light-svg" data-testid="perimeter-light">
      <path d={pathD} pathLength={1} className="perimeter-light-path" />
    </svg>
  );
}

function CenterPanel({
  broadcastSettings,
  matchState,
  panelRef,
}: {
  broadcastSettings: BroadcastSettings | null;
  matchState: MatchState;
  panelRef?: React.RefObject<HTMLDivElement | null>;
}) {
  const label =
    broadcastSettings?.tournament_label?.trim() ||
    matchState.tournament_name ||
    "";

  return (
    <div className="center-panel" ref={panelRef}>
      <div className="center-panel-brand">
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
  characterStats = null,
}: DraftOverlayProps) {
  // Refs para PerimeterLight (checkpoint HUD-9) - van antes del return
  // temprano de abajo porque los hooks de React no pueden ser
  // condicionales.
  const hudBottomBarRef = useRef<HTMLDivElement>(null);
  const leftBanRowRef = useRef<HTMLDivElement>(null);
  const centerPanelRef = useRef<HTMLDivElement>(null);
  const rightBanRowRef = useRef<HTMLDivElement>(null);

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
      {/* Logo del torneo arriba centrado (checkpoint acordado, ver
       * ROADMAP.md) - glow + divisor fino en vez de un recuadro
       * completo, para que se lea como marca/identidad y no como otra
       * tarjeta de datos compitiendo con el panel central. El panel
       * central ya tiene su propio logo chico junto al texto
       * (.center-logo, sin tocar) - este es el segundo, mas grande y
       * arriba de todo, la ubicacion principal acordada. */}
      {broadcastSettings?.logo_url && (
        <div className="hud-top-logo-wrapper">
          <img
            className="hud-top-logo"
            src={broadcastSettings.logo_url}
            alt=""
            onError={(event) => {
              event.currentTarget.style.display = "none";
            }}
          />
          <div className="hud-top-logo-divider" />
        </div>
      )}
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

      <div className="hud-bottom-bar" ref={hudBottomBarRef}>
        <PerimeterLight
          containerRef={hudBottomBarRef}
          boxRefs={[leftBanRowRef, centerPanelRef, rightBanRowRef]}
          skewPx={14}
        />
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
            rowRef={leftBanRowRef}
            characterStats={characterStats}
          />
        )}

        <CenterPanel
          broadcastSettings={broadcastSettings}
          matchState={matchState}
          panelRef={centerPanelRef}
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
            rowRef={rightBanRowRef}
            characterStats={characterStats}
          />
        )}
      </div>
    </div>
  );
}
