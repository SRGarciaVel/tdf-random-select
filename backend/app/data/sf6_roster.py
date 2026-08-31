"""Roster de personajes de Street Fighter 6.

Confirmado contra el roster oficial vigente el 31-08-2026 (31 personajes:
18 base + 4 Year 1 + 4 Year 2 + 4 Year 3 + Yasmine de Year 4, lanzada el
03-08-2026). Arjun, Tifa y Bosch (resto de Year 4) todavia no salen -
agregar cuando se lancen. Solo el campo "id" importa para la logica del
draft (DraftService); "display_name" es para UI y "portrait_filename" se
completa en la Fase 3 cuando se agregan los retratos oficiales a
overlay_app/public/portraits/.
"""

from __future__ import annotations

from typing import TypedDict


class CharacterEntry(TypedDict):
    id: str
    display_name: str
    portrait_filename: str | None


SF6_ROSTER: list[CharacterEntry] = [
    {"id": "ryu", "display_name": "Ryu", "portrait_filename": None},
    {"id": "luke", "display_name": "Luke", "portrait_filename": None},
    {"id": "kimberly", "display_name": "Kimberly", "portrait_filename": None},
    {"id": "chun_li", "display_name": "Chun-Li", "portrait_filename": None},
    {"id": "ken", "display_name": "Ken", "portrait_filename": None},
    {"id": "guile", "display_name": "Guile", "portrait_filename": None},
    {"id": "juri", "display_name": "Juri", "portrait_filename": None},
    {"id": "jp", "display_name": "JP", "portrait_filename": None},
    {"id": "marisa", "display_name": "Marisa", "portrait_filename": None},
    {"id": "manon", "display_name": "Manon", "portrait_filename": None},
    {"id": "zangief", "display_name": "Zangief", "portrait_filename": None},
    {"id": "jamie", "display_name": "Jamie", "portrait_filename": None},
    {"id": "cammy", "display_name": "Cammy", "portrait_filename": None},
    {"id": "lily", "display_name": "Lily", "portrait_filename": None},
    {"id": "dee_jay", "display_name": "Dee Jay", "portrait_filename": None},
    {"id": "blanka", "display_name": "Blanka", "portrait_filename": None},
    {"id": "dhalsim", "display_name": "Dhalsim", "portrait_filename": None},
    {"id": "e_honda", "display_name": "E. Honda", "portrait_filename": None},
    {"id": "rashid", "display_name": "Rashid", "portrait_filename": None},
    {"id": "a_k_i", "display_name": "A.K.I.", "portrait_filename": None},
    {"id": "ed", "display_name": "Ed", "portrait_filename": None},
    {"id": "akuma", "display_name": "Akuma", "portrait_filename": None},
    {"id": "m_bison", "display_name": "M. Bison", "portrait_filename": None},
    {"id": "terry", "display_name": "Terry", "portrait_filename": None},
    {"id": "mai", "display_name": "Mai", "portrait_filename": None},
    {"id": "elena", "display_name": "Elena", "portrait_filename": None},
    {"id": "sagat", "display_name": "Sagat", "portrait_filename": None},
    {"id": "c_viper", "display_name": "C. Viper", "portrait_filename": None},
    {"id": "alex", "display_name": "Alex", "portrait_filename": None},
    {"id": "ingrid", "display_name": "Ingrid", "portrait_filename": None},
    {"id": "yasmine", "display_name": "Yasmine", "portrait_filename": None},
]

CHARACTER_IDS: list[str] = [entry["id"] for entry in SF6_ROSTER]
