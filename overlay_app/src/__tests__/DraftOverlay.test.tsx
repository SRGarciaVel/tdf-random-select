import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DraftOverlay from "../DraftOverlay";
import type { CharacterInfo, MatchState } from "../types";

const roster: CharacterInfo[] = [
  { id: "ryu", display_name: "Ryu", portrait_filename: null },
  { id: "luke", display_name: "Luke", portrait_filename: null },
  { id: "chun_li", display_name: "Chun-Li", portrait_filename: null },
];

const playerA = { id: 1, display_name: "Sirxtias" };
const playerB = { id: 2, display_name: "Drachen" };

describe("DraftOverlay", () => {
  it("muestra la pantalla de espera cuando no hay match_id", () => {
    render(<DraftOverlay matchState={{ match_id: null }} roster={roster} />);
    expect(screen.getByText("Esperando partida...")).toBeInTheDocument();
  });

  it("en SETUP muestra los jugadores y la grilla completa sin baneos", () => {
    const state: MatchState = {
      match_id: 3,
      status: "SETUP",
      player_a: playerA,
      player_b: playerB,
      banned_character_ids: [],
      current_turn_player_id: null,
      results: null,
    };
    render(<DraftOverlay matchState={state} roster={roster} />);
    expect(screen.getByText(/Sirxtias vs Drachen/)).toBeInTheDocument();
    for (const character of roster) {
      const card = screen.getByTestId(`character-${character.id}`);
      expect(card).not.toHaveClass("banned");
    }
  });

  it("en BANNING muestra de quien es el turno y marca los baneados", () => {
    const state: MatchState = {
      match_id: 3,
      status: "BANNING",
      player_a: playerA,
      player_b: playerB,
      banned_character_ids: ["ryu"],
      current_turn_player_id: playerB.id,
      results: null,
    };
    render(<DraftOverlay matchState={state} roster={roster} />);
    expect(screen.getByText("Turno de banear: Drachen")).toBeInTheDocument();
    expect(screen.getByTestId("character-ryu")).toHaveClass("banned");
    expect(screen.getByTestId("character-luke")).not.toHaveClass("banned");
  });

  it("en RANDOMIZING muestra el mensaje de randomizando", () => {
    const state: MatchState = {
      match_id: 3,
      status: "RANDOMIZING",
      player_a: playerA,
      player_b: playerB,
      banned_character_ids: ["ryu", "luke"],
      current_turn_player_id: null,
      results: null,
    };
    render(<DraftOverlay matchState={state} roster={roster} />);
    expect(screen.getByText("Randomizando...")).toBeInTheDocument();
  });

  it("en REVEAL muestra el resultado de cada jugador con su retrato", () => {
    const state: MatchState = {
      match_id: 3,
      status: "REVEAL",
      player_a: playerA,
      player_b: playerB,
      banned_character_ids: ["luke"],
      current_turn_player_id: null,
      results: { "1": "ryu", "2": "chun_li" },
    };
    render(<DraftOverlay matchState={state} roster={roster} />);

    const resultA = screen.getByTestId("result-player-a");
    expect(resultA).toHaveTextContent("Sirxtias");
    expect(resultA.querySelector("img")).toHaveAttribute(
      "src",
      "/portraits/ryu.webp",
    );

    const resultB = screen.getByTestId("result-player-b");
    expect(resultB).toHaveTextContent("Drachen");
    expect(resultB.querySelector("img")).toHaveAttribute(
      "src",
      "/portraits/chun_li.webp",
    );

    // En REVEAL no se muestra la grilla, solo el resultado
    expect(screen.queryByTestId("character-ryu")).not.toBeInTheDocument();
  });

  it("en DONE sigue mostrando los mismos resultados que REVEAL", () => {
    const state: MatchState = {
      match_id: 3,
      status: "DONE",
      player_a: playerA,
      player_b: playerB,
      banned_character_ids: ["luke"],
      current_turn_player_id: null,
      results: { "1": "ryu", "2": "chun_li" },
    };
    render(<DraftOverlay matchState={state} roster={roster} />);
    expect(screen.getByTestId("result-player-a")).toHaveTextContent("Sirxtias");
  });
});
