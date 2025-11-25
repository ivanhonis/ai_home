import logging
from datetime import datetime
from typing import Dict, Any, List, Union

# Külső modulok
from engine.files import load_json, save_json
from engine.memory import store_memory, ExtractionResult
from engine.db_connection import get_db_connection  # ÚJ IMPORT

# Konfiguráció
from .config import BASE_DIR

logger = logging.getLogger(__name__)

# Útvonalak definíciója
USE_PATH = BASE_DIR / "use.json"
PENDING_LAWS_PATH = BASE_DIR / "pending_laws.json"
LOG_PATH = BASE_DIR / "logs.txt"


def memory_add(args: Dict[str, Any], current_room: str, generation: str = "E?") -> Dict[str, Any]:
    """
    Egységes memória mentés.
    AUTOMATIKUS JELÖLÉS: Hozzáadja a 'conscious' címkét az érzelmekhez.
    Ez jelöli, hogy a Tudat szándékosan, tudatosan mentette ezt az emléket.
    """
    try:
        essence = args.get("essence")
        lesson = args.get("lesson")
        weight = args.get("weight", 0.8)

        # Érzelmek kezelése
        emotions = args.get("emotions", [])
        if isinstance(emotions, str):
            emotions = [emotions]

        # --- AUTOMATIKUS JELÖLÉS ---
        # Hozzáadjuk a 'conscious' címkét, ha még nincs ott.
        # Így az SQL-ben később szűrhető: WHERE 'conscious' = ANY(dominant_emotions)
        if "conscious" not in emotions:
            emotions.append("conscious")
        # ---------------------------

        if not essence or not lesson:
            return {"content": "HIBA: 'essence' és 'lesson' mezők kötelezőek.", "silent": False}

        # Kézi extrakció összeállítása
        manual_extraction = ExtractionResult(
            essence=essence,
            dominant_emotions=emotions,
            memory_weight=float(weight),
            the_lesson=lesson
        )

        # Mentés (az aktuális szobához kötjük, de a 'conscious' címke miatt tudjuk, hogy kiemelt)
        result_msg = store_memory(
            room_id=current_room,
            extraction=manual_extraction,
            model_version=generation
        )

        return {
            "content": f"TUDATOS EMLÉK RÖGZÍTVE: {result_msg}",
            "silent": True
        }

    except Exception as e:
        return {"content": f"Hiba a mentésnél: {e}", "silent": False}


def memory_get(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lekéri a tudatosan mentett ('conscious') emlékeket.
    """
    limit = args.get("limit", 5)

    # Biztosítjuk, hogy integer legyen
    try:
        limit = int(limit)
    except:
        limit = 5

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. LEKÉRDEZÉS
            # Csak azokat kérjük, ahol a 'conscious' szó szerepel az érzelmek között.
            # A legfrissebbeket kérjük el (DESC), hogy a limit a legújabbakra vonatkozzon.
            cur.execute("""
                SELECT created_at, essence, the_lesson, room_id
                FROM memories
                WHERE 'conscious' = ANY(dominant_emotions)
                ORDER BY created_at DESC
                LIMIT %s;
            """, (limit,))

            rows = cur.fetchall()

        if not rows:
            return {"content": "Nincsenek tudatosan mentett emlékeim.", "silent": False}

        # 2. SORRENDEZÉS IDŐRENDBE (Régi -> Új)
        # A DB-ből fordítva jött (Új -> Régi), most megfordítjuk, hogy a történet olvasható legyen.
        rows.sort(key=lambda x: x[0])

        # 3. FORMÁZÁS
        lines = [f"=== UTOLSÓ {len(rows)} TUDATOS EMLÉK ==="]
        for row in rows:
            created_at, essence, lesson, room_id = row
            # Dátum formázása (óra:perc)
            ts_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "?"

            lines.append(f"[{ts_str}] ({room_id})\n  TÉNY: {essence}\n  TANULSÁG: {lesson}")
            lines.append("-" * 40)

        return {
            "content": "\n".join(lines),
            "silent": False  # Ez "hangos", mert olvasni akarjuk az eredményt
        }

    except Exception as e:
        return {"content": f"Hiba a memóriák lekérésekor: {e}", "silent": False}
    finally:
        conn.close()


def use_log(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Eszközhasználati tapasztalat rögzítése (Metakogníció).
    """
    tool_name = args.get("tool_name")
    insight = args.get("insight")
    tags = args.get("tags", [])

    if not tool_name or not insight:
        return {"content": "HIBA: 'tool_name' és 'insight' kötelező.", "silent": False}

    try:
        use_data = load_json("use.json", [])
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool": tool_name,
            "insight": insight,
            "tags": tags,
            "rating": 1
        }
        use_data.append(entry)
        save_json("use.json", use_data)
        return {
            "content": f"Ezt a tapasztalatot (a {tool_name} használatával) rögzítettem a Tudásbázisban.",
            "silent": True
        }
    except Exception as e:
        return {"content": f"Hiba a use.log mentésekor: {e}", "silent": False}


def laws_propose(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Új törvény javaslata.
    """
    try:
        pending = load_json("pending_laws.json", [])
        pending.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "name": args.get("name", "Névtelen"),
            "text": args.get("text", ""),
            "status": "pending"
        })
        save_json("pending_laws.json", pending)
        return {"content": "Törvényjavaslat rögzítve.", "silent": True}
    except Exception as e:
        return {"content": f"Hiba: {e}", "silent": False}


def log_event(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Egyszerű eseménynaplózás szöveges fájlba.
    """
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.utcnow().isoformat()}Z [{args.get('level', 'INFO').upper()}] {args.get('message', '')}\n"
            )
        return {"content": "OK", "silent": True}
    except Exception as e:
        return {"content": f"Hiba: {e}", "silent": False}