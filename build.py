#!/usr/bin/env python3
"""
Genera listas IPTV personalizadas a partir de iptv-org (solo canales públicos).
Salidas por lista: .m3u, .m3u8, .json y bouquet Enigma2 (userbouquet.*.tv)

Uso:  python build.py            (descarga de iptv-org)
      python build.py --local DIR (usa archivos .m3u locales, para pruebas)
"""
import json
import os
import re
import sys
import urllib.request

BASE = "https://iptv-org.github.io/iptv"

# ---------------------------------------------------------------------------
# CONFIGURACIÓN — edita aquí
# ---------------------------------------------------------------------------
LISTAS = [
    {
        "id": "peru_4k",
        "nombre": "Perú 4K",
        "fuentes": [f"{BASE}/countries/pe.m3u"],
        # 4K en señal abierta peruana casi no existe; por eso se ordena de
        # mayor a menor calidad y se aceptan desde 720p. Pon 2160 para solo 4K.
        "calidad_minima": 720,
        "incluir_sin_calidad": True,   # muchos canales no indican resolución
    },
    {
        "id": "deportes_hd",
        "nombre": "Deportes HD",
        "fuentes": [f"{BASE}/categories/sports.m3u"],
        "calidad_minima": 720,         # 720p, 1080p, 2160p
        "incluir_sin_calidad": False,
    },
]
SALIDA = "listas"
EPG = "https://iptv-org.github.io/epg/guides.xml"  # guía opcional
# ---------------------------------------------------------------------------

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
QUALITY_RE = re.compile(r"\((\d{3,4})[pi]\)")


def descargar(url, local_dir=None):
    if local_dir:
        ruta = os.path.join(local_dir, os.path.basename(url))
        with open(ruta, encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": "mi-iptv/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def parsear_m3u(texto):
    canales, actual, opciones = [], None, []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#EXTM3U"):
            continue
        if linea.startswith("#EXTINF"):
            info, _, nombre = linea.partition(",")
            actual = dict(ATTR_RE.findall(info))
            actual["name"] = nombre.strip()
            opciones = []
        elif linea.startswith("#EXTVLCOPT") or linea.startswith("#KODIPROP"):
            opciones.append(linea)
        elif not linea.startswith("#") and actual is not None:
            m = QUALITY_RE.search(actual["name"])
            actual["quality"] = int(m.group(1)) if m else 0
            actual["url"] = linea
            actual["opts"] = opciones
            canales.append(actual)
            actual, opciones = None, []
    return canales


def clave(c):
    tid = c.get("tvg-id", "")
    if tid:
        return tid.split("@")[0].lower()
    nombre = QUALITY_RE.sub("", c["name"])
    nombre = re.sub(r"\[.*?\]", "", nombre)
    return re.sub(r"\W+", "", nombre).lower()


def filtrar(canales, cfg):
    mejores = {}
    urls_vistas = set()
    for c in canales:
        if c["url"] in urls_vistas:
            continue
        urls_vistas.add(c["url"])
        q = c["quality"]
        if q == 0 and not cfg["incluir_sin_calidad"]:
            continue
        if q and q < cfg["calidad_minima"]:
            continue
        k = clave(c)
        if k not in mejores or q > mejores[k]["quality"]:
            mejores[k] = c
    return sorted(mejores.values(), key=lambda c: (-c["quality"], c["name"].lower()))


def escribir_m3u(canales, ruta, grupo):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG}"\n')
        for c in canales:
            attrs = " ".join(
                f'{k}="{c[k]}"' for k in ("tvg-id", "tvg-logo") if c.get(k)
            )
            g = c.get("group-title") or grupo
            f.write(f'#EXTINF:-1 {attrs} group-title="{g}",{c["name"]}\n')
            for o in c["opts"]:
                f.write(o + "\n")
            f.write(c["url"] + "\n")


def escribir_json(canales, ruta, nombre):
    data = {
        "nombre": nombre,
        "total": len(canales),
        "canales": [
            {
                "nombre": c["name"],
                "id": c.get("tvg-id", ""),
                "logo": c.get("tvg-logo", ""),
                "grupo": c.get("group-title", ""),
                "calidad": f'{c["quality"]}p' if c["quality"] else None,
                "url": c["url"],
                "opciones": c["opts"],
            }
            for c in canales
        ],
    }
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def escribir_enigma2(canales, ruta, nombre):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"#NAME {nombre}\n")
        for c in canales:
            url = c["url"].replace(":", "%3a")
            n = c["name"].replace(":", " ")
            f.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:{url}:{n}\n")
            f.write(f"#DESCRIPTION {n}\n")


def main():
    local = None
    if "--local" in sys.argv:
        local = sys.argv[sys.argv.index("--local") + 1]
    os.makedirs(os.path.join(SALIDA, "enigma2"), exist_ok=True)
    bouquets = []
    for cfg in LISTAS:
        todos = []
        for url in cfg["fuentes"]:
            try:
                todos += parsear_m3u(descargar(url, local))
            except Exception as e:
                print(f"  ! No se pudo leer {url}: {e}")
        canales = filtrar(todos, cfg)
        base = os.path.join(SALIDA, cfg["id"])
        escribir_m3u(canales, base + ".m3u", cfg["nombre"])
        escribir_m3u(canales, base + ".m3u8", cfg["nombre"])
        escribir_json(canales, base + ".json", cfg["nombre"])
        bq = f"userbouquet.{cfg['id']}.tv"
        escribir_enigma2(canales, os.path.join(SALIDA, "enigma2", bq), cfg["nombre"])
        bouquets.append(bq)
        print(f"{cfg['nombre']}: {len(canales)} canales (de {len(todos)} leídos)")
    with open(os.path.join(SALIDA, "enigma2", "bouquets.tv.agregar.txt"), "w") as f:
        f.write("# Pega estas líneas al final de /etc/enigma2/bouquets.tv\n")
        for bq in bouquets:
            f.write(f'#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{bq}" ORDER BY bouquet\n')


if __name__ == "__main__":
    main()
