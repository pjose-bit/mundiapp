"""
main.py – Sistema de análisis del Mundial 2026.

Uso:
    python main.py                    → menú interactivo para elegir partido
    python main.py "France" "Sweden"  → analiza ese partido directamente
"""

import sys
import io
import os
import webbrowser

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from colorama import init, Fore, Style
from scraper_apuestas import obtener_partidos_con_estado, guardar_csv
from scraper_prensa import analizar_prensa, analizar_prensa_todos, guardar_csv_prensa
from generar_reporte import guardar_reporte

init(autoreset=True)


def banner():
    print(Fore.YELLOW + Style.BRIGHT + """
  =========================================
    ANALISIS MUNDIAL 2026 - PREDICCIONES
    Casas de Apuestas + Prensa Deportiva
  =========================================""")


def mostrar_menu(partidos: list):
    print(Fore.CYAN + Style.BRIGHT + f"\n  {'#':>3}  {'PARTIDO':<35} {'FECHA':<12} {'FAV':<22} {'CUOTA'}")
    print("  " + "─" * 80)
    for i, p in enumerate(partidos, 1):
        vivo  = Fore.RED + " ● VIVO" + Fore.WHITE if p.get("en_vivo") else ""
        mas   = p.get("mas_probable", "?")
        cuota = p.get("cuota_mas_probable", "?")
        print(Fore.WHITE + f"  {i:>3}.  {p['partido']:<35} {p['fecha']:<12} {mas:<22} {cuota}{vivo}")
    print()


def analizar(partido: dict, todos: list):
    local  = partido["local"]
    visita = partido["visitante"]
    vivo   = " [EN VIVO]" if partido.get("en_vivo") else ""

    print(Fore.CYAN + f"\n  Analizando: {local} vs {visita}{vivo}\n")

    pr  = partido["promedios"]
    pb  = partido["probabilidades"]
    mas = partido["mas_probable"]

    print(Fore.GREEN + f"  Cuotas →  1:{pr['1']}  X:{pr['X']}  2:{pr['2']}")
    print(Fore.GREEN + f"  Favorito: {mas} (cuota {partido['cuota_mas_probable']})")
    print(Fore.WHITE + f"  Probs  →  " + "  |  ".join(f"{k}: {v}%" for k, v in pb.items()))
    guardar_csv(partido)

    print(Fore.WHITE + Style.BRIGHT + "\n  Buscando noticias de prensa para todos los partidos...")
    todas_prensas = analizar_prensa_todos(todos)
    prensa = todas_prensas.get(f"{local} vs {visita}") or analizar_prensa(local, visita)
    guardar_csv_prensa(prensa)

    print(Fore.WHITE + Style.BRIGHT + "\n  Generando dashboard...")
    ruta = guardar_reporte(partido, prensa, todos, todas_prensas)

    print(Fore.CYAN + Style.BRIGHT + f"\n  Dashboard listo:")
    print(f"  {ruta}\n")
    webbrowser.open(ruta)


def buscar_por_nombre(partidos: list, e1: str, e2: str):
    e1, e2 = e1.lower(), e2.lower()
    for p in partidos:
        h = p["local"].lower()
        a = p["visitante"].lower()
        if (e1 in h or e1 in a) and (e2 in h or e2 in a):
            return p
    return None


if __name__ == "__main__":
    banner()

    print(Fore.WHITE + "\n  Consultando partidos disponibles...")
    todos = obtener_partidos_con_estado()

    if not todos:
        print(Fore.RED + "  No se encontraron partidos. Verifica ODDS_API_KEY en config.py")
        sys.exit(1)

    # ── Modo directo: python main.py "France" "Sweden" ────────────────
    if len(sys.argv) == 3:
        partido = buscar_por_nombre(todos, sys.argv[1], sys.argv[2])
        if not partido:
            print(Fore.RED + f"  Partido no encontrado: {sys.argv[1]} vs {sys.argv[2]}")
            print(Fore.YELLOW + "  Partidos disponibles:")
            mostrar_menu(todos)
        else:
            analizar(partido, todos)
        sys.exit(0)

    # ── Modo menú interactivo ─────────────────────────────────────────
    while True:
        mostrar_menu(todos)
        print(Fore.CYAN + "  Ingresa el número del partido a analizar (o 'q' para salir): ", end="")
        opcion = input().strip()

        if opcion.lower() == "q":
            break

        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(todos):
                analizar(todos[idx], todos)
                print(Fore.CYAN + "\n  Presiona Enter para volver al menú...")
                input()
            else:
                print(Fore.RED + f"  Número inválido. Elige entre 1 y {len(todos)}.\n")
        except ValueError:
            print(Fore.RED + "  Ingresa un número válido.\n")
