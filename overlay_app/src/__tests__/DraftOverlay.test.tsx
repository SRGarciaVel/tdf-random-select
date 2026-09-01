import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import DraftOverlay from "../DraftOverlay";
import type { BroadcastSettings, CharacterInfo, MatchState } from "../types";

const roster: CharacterInfo[] = [
  { id: "ryu", display_name: "Ryu", portrait_filename: null },
  { id: "luke", display_name: "Luke", portrait_filename: null },
  { id: "chun_li", display_name: "Chun-Li", portrait_filename: null },
];

const playerA = { id: 1, display_name: "Sirxtias" };
const playerB = { id: 2, display_name: "Drachen" };

const baseState: MatchState = {
  match_id: 3,
  status: "SETUP",
  player_a: playerA,
  player_b: playerB,
  tournament_name: "Torneo de prueba",
  bans_per_player: 2,
  banned_character_ids: [],
  bans: [],
  current_turn_player_id: null,
  results: null,
  turn_deadline_ms: null,
};

const defaultBroadcastSettings: BroadcastSettings = {
  tournament_label: null,
  logo_choice: "tdf",
  logo_url: null,
  accent_color: "#c400ff",
  panel_background_color: "rgba(5, 5, 6, 0.85)",
};

describe("DraftOverlay (HUD)", () => {
  it("muestra la pantalla de espera cuando no hay match_id", () => {
    render(
      <DraftOverlay
        matchState={{ match_id: null }}
        roster={roster}
        broadcastSettings={null}
      />,
    );
    expect(screen.getByText("Esperando partida...")).toBeInTheDocument();
  });

  it("en SETUP dibuja bans_per_player slots vacios por jugador, sin panel dramatico", () => {
    render(
      <DraftOverlay
        matchState={baseState}
        roster={roster}
        broadcastSettings={defaultBroadcastSettings}
      />,
    );
    const emptySlots = document.querySelectorAll(".ban-slot.empty");
    expect(emptySlots).toHaveLength(4); // 2 por jugador
    expect(screen.getByText("Sirxtias")).toBeInTheDocument();
    expect(screen.getByText("Drachen")).toBeInTheDocument();
    expect(screen.queryByTestId("dramatic-left")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dramatic-right")).not.toBeInTheDocument();
  });

  it("un baneo real llena el slot con el retrato y el tajo", () => {
    const state: MatchState = {
      ...baseState,
      status: "BANNING",
      bans: [
        {
          character_id: "ryu",
          banned_by_player_id: playerA.id,
          was_timeout: false,
        },
      ],
      current_turn_player_id: playerB.id,
    };
    render(
      <DraftOverlay
        matchState={state}
        roster={roster}
        broadcastSettings={defaultBroadcastSettings}
      />,
    );
    expect(screen.getByTestId("ban-slot-ryu")).toBeInTheDocument();
    expect(
      screen.getByTestId("ban-slot-ryu").querySelector(".ban-slash"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("timeout-icon")).not.toBeInTheDocument();
  });

  it("un turno saltado por timeout muestra el marcador de skip y el icono de timeout, sin retrato", () => {
    const state: MatchState = {
      ...baseState,
      status: "BANNING",
      bans: [
        {
          character_id: null,
          banned_by_player_id: playerA.id,
          was_timeout: true,
        },
      ],
      current_turn_player_id: playerB.id,
    };
    render(
      <DraftOverlay
        matchState={state}
        roster={roster}
        broadcastSettings={defaultBroadcastSettings}
      />,
    );
    expect(screen.getByTestId("skipped-marker")).toBeInTheDocument();
    expect(screen.getByTestId("timeout-icon")).toBeInTheDocument();
  });

  it("un auto-baneo por timeout muestra el retrato Y el icono de timeout", () => {
    const state: MatchState = {
      ...baseState,
      status: "BANNING",
      bans: [
        {
          character_id: "luke",
          banned_by_player_id: playerA.id,
          was_timeout: true,
        },
      ],
      current_turn_player_id: playerB.id,
    };
    render(
      <DraftOverlay
        matchState={state}
        roster={roster}
        broadcastSettings={defaultBroadcastSettings}
      />,
    );
    expect(screen.getByTestId("ban-slot-luke")).toBeInTheDocument();
    expect(screen.getByTestId("timeout-icon")).toBeInTheDocument();
  });

  it("solo el slot que le toca al jugador activo tiene la clase active", () => {
    const state: MatchState = {
      ...baseState,
      status: "BANNING",
      bans: [
        {
          character_id: "ryu",
          banned_by_player_id: playerA.id,
          was_timeout: false,
        },
      ],
      current_turn_player_id: playerB.id,
    };
    render(
      <DraftOverlay
        matchState={state}
        roster={roster}
        broadcastSettings={defaultBroadcastSettings}
      />,
    );
    expect(document.querySelectorAll(".ban-slot.active")).toHaveLength(1);
  });

  describe("countdown", () => {
    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2026-08-31T12:00:00Z"));
    });
    afterEach(() => {
      vi.useRealTimers();
    });

    it("muestra la cuenta regresiva del slot activo y baja con el tiempo", () => {
      const deadline = Date.now() + 10_000;
      const state: MatchState = {
        ...baseState,
        status: "BANNING",
        current_turn_player_id: playerA.id,
        turn_deadline_ms: deadline,
      };
      render(
        <DraftOverlay
          matchState={state}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
        />,
      );
      expect(screen.getByTestId("countdown")).toHaveTextContent("10");

      act(() => {
        vi.advanceTimersByTime(4000);
      });
      expect(screen.getByTestId("countdown")).toHaveTextContent("6");
    });
  });

  describe("panel dramatico (checkpoint HUD-5: preview + reveal unificados)", () => {
    it("el candidato seleccionado muestra el panel dramatico solo del lado correspondiente", () => {
      const state: MatchState = {
        ...baseState,
        status: "BANNING",
        current_turn_player_id: playerA.id,
      };
      render(
        <DraftOverlay
          matchState={state}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
          candidatePreview={{ character_id: "ryu", player_id: playerA.id }}
        />,
      );
      expect(screen.getByTestId("dramatic-left")).toBeInTheDocument();
      expect(screen.queryByTestId("dramatic-right")).not.toBeInTheDocument();
    });

    it("no muestra panel dramatico si candidatePreview.character_id es null", () => {
      const state: MatchState = { ...baseState, status: "BANNING" };
      render(
        <DraftOverlay
          matchState={state}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
          candidatePreview={{ character_id: null, player_id: playerA.id }}
        />,
      );
      expect(screen.queryByTestId("dramatic-left")).not.toBeInTheDocument();
      expect(screen.queryByTestId("dramatic-right")).not.toBeInTheDocument();
    });

    it("en REVEAL muestra el panel dramatico de ambos lados con el resultado, ignorando cualquier candidatePreview viejo", () => {
      const state: MatchState = {
        ...baseState,
        status: "REVEAL",
        results: { "1": "ryu", "2": "chun_li" },
      };
      render(
        <DraftOverlay
          matchState={state}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
          candidatePreview={{ character_id: "luke", player_id: playerA.id }}
        />,
      );

      const left = screen.getByTestId("dramatic-left");
      expect(left.querySelector("img")).toHaveAttribute(
        "src",
        "/portraits-large/ryu.png",
      );
      expect(left).toHaveTextContent("Ryu");
      expect(left).not.toHaveTextContent("Luke"); // el candidatePreview viejo no se cuela

      const right = screen.getByTestId("dramatic-right");
      expect(right.querySelector("img")).toHaveAttribute(
        "src",
        "/portraits-large/chun_li.png",
      );
      expect(right).toHaveTextContent("Chun-Li");
    });

    it("en DONE sigue mostrando el panel dramatico del resultado", () => {
      const state: MatchState = {
        ...baseState,
        status: "DONE",
        results: { "1": "ryu", "2": "chun_li" },
      };
      render(
        <DraftOverlay
          matchState={state}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
        />,
      );
      expect(screen.getByTestId("dramatic-left")).toBeInTheDocument();
      expect(screen.getByTestId("dramatic-right")).toBeInTheDocument();
    });
  });

  describe("panel central", () => {
    it("usa el tournament_label de broadcast settings si esta configurado", () => {
      const settings: BroadcastSettings = {
        ...defaultBroadcastSettings,
        tournament_label: "Randomizer TDF 2026",
      };
      render(
        <DraftOverlay
          matchState={baseState}
          roster={roster}
          broadcastSettings={settings}
        />,
      );
      expect(screen.getByText("Randomizer TDF 2026")).toBeInTheDocument();
      expect(screen.queryByText("Torneo de prueba")).not.toBeInTheDocument();
    });

    it("cae al nombre real del torneo si no hay tournament_label configurado", () => {
      render(
        <DraftOverlay
          matchState={baseState}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
        />,
      );
      expect(screen.getByText("Torneo de prueba")).toBeInTheDocument();
    });

    it("muestra el estado del draft en el panel central", () => {
      const state: MatchState = { ...baseState, status: "RANDOMIZING" };
      render(
        <DraftOverlay
          matchState={state}
          roster={roster}
          broadcastSettings={defaultBroadcastSettings}
        />,
      );
      expect(screen.getByText("Randomizando...")).toBeInTheDocument();
    });
  });

  describe("colores personalizables", () => {
    it("aplica accent_color y panel_background_color como custom properties del HUD", () => {
      const settings: BroadcastSettings = {
        ...defaultBroadcastSettings,
        accent_color: "#00ffaa",
        panel_background_color: "rgba(10, 10, 10, 0.9)",
      };
      render(
        <DraftOverlay
          matchState={baseState}
          roster={roster}
          broadcastSettings={settings}
        />,
      );
      const hudRoot = document.querySelector(".hud-root") as HTMLElement;
      expect(hudRoot.style.getPropertyValue("--hud-accent-color")).toBe(
        "#00ffaa",
      );
      expect(hudRoot.style.getPropertyValue("--hud-panel-bg-color")).toBe(
        "rgba(10, 10, 10, 0.9)",
      );
    });

    it("usa los colores por defecto del club si no hay broadcastSettings", () => {
      render(
        <DraftOverlay
          matchState={baseState}
          roster={roster}
          broadcastSettings={null}
        />,
      );
      const hudRoot = document.querySelector(".hud-root") as HTMLElement;
      expect(hudRoot.style.getPropertyValue("--hud-accent-color")).toBe(
        "#c400ff",
      );
    });
  });
});
