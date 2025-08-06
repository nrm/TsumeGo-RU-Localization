import sys
import os

# --- Финальные параметры ---

CMAP_OFFSET = 15664
WIDTH_TABLE_OFFSET = 16746
CGLP_OFFSET = 59

NUM_GLYPHS = 541
BYTES_PER_GLYPH_BITMAP = 25
CELL_WIDTH = 13
CELL_HEIGHT = 15
PIXEL_ON = "██"
PIXEL_OFF = "  "

def draw_bitmap(glyph_data):
    """Сначала столбцы 8–12 из строки y, затем 0–7 из строки y+1 (или пусто, если вышли за пределы)."""
    if len(glyph_data) < BYTES_PER_GLYPH_BITMAP:
        print("Ошибка: недостаточно данных для отрисовки битмапа.")
        return

    pixels = []
    for byte in glyph_data:
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            pixels.append(bit)

    is_empty = all(p == 0 for p in pixels[:CELL_WIDTH * CELL_HEIGHT])
    print(f"\nБитмап символа (13x15): {'(ПУСТОЙ)' if is_empty else ''}")
    print("+" + "-" * (CELL_WIDTH * 2) + "+")

    for y in range(CELL_HEIGHT):
        print("|", end="")
        # Столбцы 8–12 из строки y
        for x in range(8, 13):
            idx = y * CELL_WIDTH + x
            if idx < len(pixels):
                print(PIXEL_ON if pixels[idx] else PIXEL_OFF, end="")
        # Столбцы 0–7 из строки y+1
        if y < CELL_HEIGHT - 1:
            for x in range(0, 8):
                idx = (y + 1) * CELL_WIDTH + x
                if idx < len(pixels):
                    print(PIXEL_ON if pixels[idx] else PIXEL_OFF, end="")
        else:
            print(PIXEL_OFF * 8, end="")
        print("|")
    print("+" + "-" * (CELL_WIDTH * 2) + "+")

def main():
    if len(sys.argv) != 3:
        print(f"Использование: python {sys.argv[0]} <файл.nftr> <индекс_глифа>")
        sys.exit(1)

    font_file, glyph_index_str = sys.argv[1], sys.argv[2]

    try:
        glyph_index = int(glyph_index_str)
    except ValueError:
        print(f"Ошибка: Индекс '{glyph_index_str}' не является целым числом.")
        sys.exit(1)

    if not os.path.exists(font_file):
        print(f"Ошибка: Файл '{font_file}' не найден.")
        sys.exit(1)

    if not (0 <= glyph_index < NUM_GLYPHS):
        print(f"Ошибка: Индекс должен быть в диапазоне от 0 до {NUM_GLYPHS - 1}.")
        sys.exit(1)

    with open(font_file, 'rb') as f:
        data = f.read()

    sjis_code_addr = CMAP_OFFSET + (glyph_index * 2)
    width_addr = WIDTH_TABLE_OFFSET + (glyph_index * 1)
    bitmap_addr = CGLP_OFFSET + (glyph_index * BYTES_PER_GLYPH_BITMAP)

    sjis_code = int.from_bytes(data[sjis_code_addr:sjis_code_addr+2], 'little')
    width = data[width_addr]
    bitmap_data = data[bitmap_addr : bitmap_addr + BYTES_PER_GLYPH_BITMAP]

    print(f"\n--- Полный анализ глифа с индексом {glyph_index} ---")

    char_repr = f"(код: 0x{sjis_code:X})"
    if sjis_code != 0:
        try:
            if 0x20 <= sjis_code <= 0x7E:
                char_repr = f"'{chr(sjis_code)}' (код ASCII: 0x{sjis_code:X})"
            else:
                char_repr = f"'{sjis_code.to_bytes(2, 'big').decode('shift_jis')}' (код SJIS: 0x{sjis_code:X})"
        except (UnicodeDecodeError, OverflowError):
            char_repr = f"(неизвестный код: 0x{sjis_code:X})"

    print(f"Код символа: {char_repr.ljust(30)} | Смещение в файле: {sjis_code_addr} (0x{sjis_code_addr:X})")
    print(f"Ширина глифа: {width} пикселей{''.ljust(23)} | Смещение в файле: {width_addr} (0x{width_addr:X})")
    print(f"Данные битмапа: {len(bitmap_data)} байт{''.ljust(26)}| Смещение в файле: {bitmap_addr} (0x{bitmap_addr:X})")

    draw_bitmap(bitmap_data)

if __name__ == "__main__":
    main()

