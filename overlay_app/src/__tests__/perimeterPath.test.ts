import { describe, expect, it } from "vitest";
import { buildPerimeterPath, type PerimeterBox } from "../DraftOverlay";

// Estos tests cubren la geometria del contorno (checkpoint HUD-9) sin
// depender de un layout real de navegador (jsdom no calcula posiciones
// reales) - lo que SI podemos probar de verdad es que la funcion arma
// un camino SVG cerrado y consistente a partir de cajas ya medidas.

const box = (
  left: number,
  right: number,
  top: number,
  bottom: number,
): PerimeterBox => ({ left, right, top, bottom });

describe("buildPerimeterPath", () => {
  it("con cero cajas devuelve string vacio (nada que dibujar)", () => {
    expect(buildPerimeterPath([], 14)).toBe("");
  });

  it("con una sola caja arranca y cierra el camino (M ... Z)", () => {
    const path = buildPerimeterPath([box(0, 100, 0, 50)], 14);
    expect(path.startsWith("M 0 50")).toBe(true);
    expect(path.endsWith("Z")).toBe(true);
  });

  it("respeta el angulo de corte en los bordes izquierdo y derecho de una caja sola", () => {
    const path = buildPerimeterPath([box(0, 100, 0, 50)], 14);
    // sube por el borde izquierdo cortado en diagonal (14px de skew)
    expect(path).toContain("L 14 0");
    // baja por el borde derecho cortado en diagonal (100 - 14)
    expect(path).toContain("L 86 50");
  });

  it("con tres cajas (mazo izq + centro + mazo der), conecta cada una con la siguiente", () => {
    const boxes = [
      box(0, 100, 10, 60), // mazo izquierdo
      box(100, 200, 0, 70), // panel central (mas alto)
      box(200, 300, 10, 60), // mazo derecho
    ];
    const path = buildPerimeterPath(boxes, 14);
    // arranca abajo-izquierda de la primera caja
    expect(path.startsWith("M 0 60")).toBe(true);
    // el borde de arriba de la primera caja termina en su esquina
    // superior derecha (right=100) antes de saltar a la siguiente
    expect(path).toContain("L 100 10");
    // salta a la esquina superior izquierda (cortada) de la 2da caja
    expect(path).toContain("L 114 0");
    // termina bajando por el borde derecho cortado de la ULTIMA caja
    expect(path).toContain("L 286 60");
    expect(path.endsWith("Z")).toBe(true);
  });

  it("con dos cajas (por ejemplo, un lado todavia sin baneos confirmados) sigue armando un camino valido", () => {
    const boxes = [box(50, 150, 0, 40), box(150, 250, 0, 45)];
    const path = buildPerimeterPath(boxes, 10);
    expect(path.startsWith("M 50 40")).toBe(true);
    expect(path.endsWith("Z")).toBe(true);
    // conecta el borde derecho de la primera con el izquierdo (cortado) de la segunda
    expect(path).toContain("L 150 0");
    expect(path).toContain("L 160 0");
  });
});
