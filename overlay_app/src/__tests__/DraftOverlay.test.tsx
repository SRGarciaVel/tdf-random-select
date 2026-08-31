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

const noBroadcastSettings: BroadcastSettings | null = null;

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

  it("en SETUP dibuja bans_per_player slots vacios por jugador", () => {
    render(
      <DraftOverlay
        matchState={baseState}
        roster={roster}
        broadcastSettings={noBroadcastSettings}
      />,
    );
    const emptySlots = document.querySelectorAll(".ban-slot.empty");
    expect(emptySlots).toHaveLength(4); // 2 por jugador
    expect(screen.getByText("Sirxtias")).toBeInTheDocument();
    expect(screen.getByText("Drachen")).toBeInTheDocument();
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
        broadcastSettings={noBroadcastSettings}
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
        broadcastSettings={noBroadcastSettings}
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
        broadcastSettings={noBroadcastSettings}
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
        broadcastSettings={noBroadcastSettings}
      />,
    );
    const activeSlots = document.querySelectorAll(".ban-slot.active");
    expect(activeSlots).toHaveLength(1);
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
      const deadline = Date.now() + 10_000; // 10s en el futuro
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
          broadcastSettings={noBroadcastSettings}
        />,
      );
      expect(screen.getByTestId("countdown")).toHaveTextContent("10");

      act(() => {
        vi.advanceTimersByTime(4000);
      });
      expect(screen.getByTestId("countdown")).toHaveTextContent("6");
    });
  });

  it("en REVEAL muestra el resultado de cada jugador en su lado, sin la fila de slots", () => {
    const state: MatchState = {
      ...baseState,
      status: "REVEAL",
      bans: [
        {
          character_id: "ryu",
          banned_by_player_id: playerA.id,
          was_timeout: false,
        },
        {
          character_id: "luke",
          banned_by_player_id: playerB.id,
          was_timeout: false,
        },
      ],
      current_turn_player_id: null,
      results: { "1": "ryu", "2": "chun_li" },
    };
    render(
      <DraftOverlay
        matchState={state}
        roster={roster}
        broadcastSettings={noBroadcastSettings}
      />,
    );

    const resultLeft = screen.getByTestId("result-left");
    expect(resultLeft).toHaveTextContent("Sirxtias");
    expect(resultLeft.querySelector("img")).toHaveAttribute(
      "src",
      "/portraits/ryu.webp",
    );

    const resultRight = screen.getByTestId("result-right");
    expect(resultRight).toHaveTextContent("Drachen");
    expect(resultRight.querySelector("img")).toHaveAttribute(
      "src",
      "/portraits/chun_li.webp",
    );

    expect(document.querySelectorAll(".ban-slot")).toHaveLength(0);
  });

  describe("panel central", () => {
    it("usa el tournament_label de broadcast settings si esta configurado", () => {
      const settings: BroadcastSettings = {
        tournament_label: "Randomizer TDF 2026",
        logo_choice: "torneo",
        logo_url: "/branding/torneo-logo.webp",
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
      const settings: BroadcastSettings = {
        tournament_label: null,
        logo_choice: "tdf",
        logo_url: null,
      };
      render(
        <DraftOverlay
          matchState={baseState}
          roster={roster}
          broadcastSettings={settings}
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
          broadcastSettings={noBroadcastSettings}
        />,
      );
      expect(screen.getByText("Randomizando...")).toBeInTheDocument();
    });
  });
});
