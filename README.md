# mi-iptv

Listas IPTV personalizadas, generadas a diario desde [iptv-org](https://github.com/iptv-org/iptv) (solo canales públicos y gratuitos).

| Lista | M3U | M3U8 | JSON | Enigma2 |
|---|---|---|---|---|
| Perú 4K | `listas/peru_4k.m3u` | `listas/peru_4k.m3u8` | `listas/peru_4k.json` | `listas/enigma2/userbouquet.peru_4k.tv` |
| Deportes HD | `listas/deportes_hd.m3u` | `listas/deportes_hd.m3u8` | `listas/deportes_hd.json` | `listas/enigma2/userbouquet.deportes_hd.tv` |

## URL para tu reproductor

```
https://raw.githubusercontent.com/TU_USUARIO/mi-iptv/main/listas/deportes_hd.m3u
https://raw.githubusercontent.com/TU_USUARIO/mi-iptv/main/listas/peru_4k.m3u
```

## Enigma2

1. Copia `listas/enigma2/userbouquet.*.tv` a `/etc/enigma2/` del decodificador.
2. Agrega a `/etc/enigma2/bouquets.tv` las líneas de `bouquets.tv.agregar.txt`.
3. Recarga: `wget -qO - "http://127.0.0.1/web/servicelistreload?mode=0"` o reinicia la GUI.

## Cambiar filtros

Edita el bloque `LISTAS` en `build.py`: fuentes, calidad mínima (720, 1080, 2160) y si se incluyen canales sin resolución indicada.
