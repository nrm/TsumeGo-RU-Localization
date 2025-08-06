#!/usr/bin/env python3
"""
Скрипт для массовой вставки русских букв в файл NFTR согласно таблице соответствия
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# --- Параметры NFTR файла ---
CMAP_OFFSET = 15664
WIDTH_TABLE_OFFSET = 16746
CGLP_OFFSET = 59
NUM_GLYPHS = 541
BYTES_PER_GLYPH_BITMAP = 25
CELL_WIDTH = 13
CELL_HEIGHT = 15

# --- Параметры генерации шрифта ---
FONT_PATH = "fonts/PressStart2P-Regular.ttf"
FONT_SIZE_UPPER = 12  # Размер для заглавных букв
FONT_SIZE_LOWER = 10  # Размер для строчных букв (чуть меньше)
BITMAP_WIDTH = 13
BITMAP_HEIGHT = 15

# --- Таблица соответствия ---
CYRILLIC_MAPPING = [
    # Заглавные буквы
    (32, "А"), (33, "Б"), (34, "В"), (35, "Г"), (36, "Д"), (37, "Е"), (38, "Ё"),
    (39, "Ж"), (40, "З"), (41, "И"), (42, "Й"), (43, "К"), (44, "Л"), (45, "М"),
    (46, "Н"), (47, "О"), (48, "П"), (49, "Р"), (50, "С"), (51, "Т"), (52, "У"),
    (53, "Ф"), (54, "Х"), (55, "Ц"), (56, "Ч"), (57, "Ш"), (58, "Щ"), (59, "Ъ"),
    (60, "Ы"), (61, "Ь"), (62, "Э"), (63, "Ю"), (64, "Я"),
    
    # Строчные буквы
    (65, "а"), (66, "б"), (67, "в"), (68, "г"), (69, "д"), (70, "е"), (71, "ё"),
    (72, "ж"), (73, "з"), (74, "и"), (75, "й"), (76, "к"), (77, "л"), (78, "м"),
    (79, "н"), (80, "о"), (81, "п"), (82, "р"), (83, "с"), (84, "т"), (85, "у"),
    (86, "ф"), (87, "х"), (88, "ц"), (89, "ч"), (90, "ш"), (91, "щ"), (92, "ъ"),
    (93, "ы"), (94, "ь"), (95, "э"), (96, "ю"), (97, "я")
]

def generate_char_bitmap(char, font_path, font_size, width, height):
    """
    Генерирует битмап символа и возвращает его как список пикселей (0 или 1)
    """
    # Создание холста и загрузка шрифта
    image = Image.new('L', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"ОШИБКА: Шрифт не найден по пути: {font_path}")
        return None, 0

    # Позиционирование: вплотную к левой границе, опущено по вертикали
    try:
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(char, font=font)
        
    # Вплотную к левой границе (x = 0), опущено по вертикали
    x_pos_draw = 0  # Левая граница
    y_pos_draw = (height - text_height) / 2 + 2  # Опущено на 2 пикселя от центра
    draw.text((x_pos_draw, y_pos_draw), char, font=font, fill='black')

    # Преобразование в битмап (обычный порядок - слева направо, сверху вниз)
    pixels = []
    for y in range(height):
        for x in range(width):
            pixel_value = 1 if image.getpixel((x, y)) < 128 else 0
            pixels.append(pixel_value)

    # Расчет фактической ширины
    min_x, max_x = width, -1
    for y in range(height):
        for x in range(width):
            if image.getpixel((x, y)) < 128:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
    actual_width = (max_x - min_x + 1) if max_x != -1 else 0

    return pixels, actual_width

def pixels_to_nftr_bytes(pixels):
    """
    Преобразует обычный битмап в формат NFTR
    """
    if len(pixels) != CELL_WIDTH * CELL_HEIGHT:
        print(f"ОШИБКА: Ожидается {CELL_WIDTH * CELL_HEIGHT} пикселей, получено {len(pixels)}")
        return None

    # Создаем массив данных 13x15
    data_pixels = [0] * (CELL_WIDTH * CELL_HEIGHT)
    
    # Заполняем массив данных на основе схемы отображения
    for display_y in range(CELL_HEIGHT):
        # Первые 5 пикселей строки отображения берутся из столбцов 8-12 строки данных display_y
        for i in range(5):
            display_x = i
            data_x = 8 + i
            data_y = display_y
            
            if display_x < CELL_WIDTH and display_y < CELL_HEIGHT:
                display_pixel = pixels[display_y * CELL_WIDTH + display_x]
                data_idx = data_y * CELL_WIDTH + data_x
                if 0 <= data_idx < len(data_pixels):
                    data_pixels[data_idx] = display_pixel
        
        # Следующие 8 пикселей строки отображения берутся из столбцов 0-7 строки данных display_y+1
        if display_y < CELL_HEIGHT - 1:
            for i in range(8):
                display_x = 5 + i
                data_x = i
                data_y = display_y + 1
                
                if display_x < CELL_WIDTH and display_y < CELL_HEIGHT:
                    display_pixel = pixels[display_y * CELL_WIDTH + display_x]
                    data_idx = data_y * CELL_WIDTH + data_x
                    if 0 <= data_idx < len(data_pixels):
                        data_pixels[data_idx] = display_pixel

    # Упаковываем data_pixels в байты
    bytes_data = []
    for i in range(0, len(data_pixels), 8):
        byte_val = 0
        for j in range(8):
            if i + j < len(data_pixels) and data_pixels[i + j]:
                byte_val |= (1 << (7 - j))
        bytes_data.append(byte_val)
    
    # Дополняем до нужного размера
    while len(bytes_data) < BYTES_PER_GLYPH_BITMAP:
        bytes_data.append(0)
    
    return bytes_data[:BYTES_PER_GLYPH_BITMAP]

def preview_bitmap(pixels, char):
    """
    Показывает превью битмапа в консоли
    """
    print(f"Превью битмапа для '{char}':")
    print("+" + "-" * (CELL_WIDTH * 2) + "+")
    
    for y in range(CELL_HEIGHT):
        print("|", end="")
        for x in range(CELL_WIDTH):
            idx = y * CELL_WIDTH + x
            if idx < len(pixels):
                print("██" if pixels[idx] else "  ", end="")
        print("|")
    
    print("+" + "-" * (CELL_WIDTH * 2) + "+")

def insert_single_glyph(data, glyph_index, char, font_path=FONT_PATH, show_preview=False):
    """
    Вставляет ТОЛЬКО битмап одного символа в данные NFTR
    """
    if not (0 <= glyph_index < NUM_GLYPHS):
        print(f"ОШИБКА: Индекс {glyph_index} выходит за границы.")
        return False

    # Выбираем размер шрифта в зависимости от регистра
    font_size = FONT_SIZE_UPPER if char.isupper() else FONT_SIZE_LOWER

    # Генерируем битмап
    pixels, actual_width = generate_char_bitmap(char, font_path, font_size, BITMAP_WIDTH, BITMAP_HEIGHT)
    if pixels is None:
        return False

    if show_preview:
        preview_bitmap(pixels, char)

    # Преобразуем в байты
    bitmap_bytes = pixels_to_nftr_bytes(pixels)
    if bitmap_bytes is None:
        return False

    # Вычисляем адрес битмапа
    bitmap_addr = CGLP_OFFSET + (glyph_index * BYTES_PER_GLYPH_BITMAP)

    # Проверяем границы
    if bitmap_addr + BYTES_PER_GLYPH_BITMAP > len(data):
        print(f"ОШИБКА: Адрес битмапа ({bitmap_addr}) выходит за границы файла ({len(data)})")
        return False

    # Записываем ТОЛЬКО битмап
    for i, byte_val in enumerate(bitmap_bytes):
        data[bitmap_addr + i] = byte_val

    print(f"✓ Символ '{char}' → индекс {glyph_index} (фактическая ширина: {actual_width}px)")
    return True

def batch_insert_cyrillic(nftr_file, font_path=FONT_PATH, start_index=None, end_index=None, preview_mode=False):
    """
    Массовая вставка всех русских букв в файл NFTR
    """
    if not os.path.exists(nftr_file):
        print(f"ОШИБКА: Файл '{nftr_file}' не найден.")
        return False

    # Читаем файл
    with open(nftr_file, 'rb') as f:
        data = bytearray(f.read())

    # Создаем резервную копию
    backup_file = nftr_file + '.backup'
    if not os.path.exists(backup_file):
        with open(backup_file, 'wb') as f:
            with open(nftr_file, 'rb') as orig:
                f.write(orig.read())
        print(f"Создана резервная копия: {backup_file}")

    # Определяем диапазон для обработки
    mapping_to_process = CYRILLIC_MAPPING
    if start_index is not None or end_index is not None:
        start_idx = start_index if start_index is not None else CYRILLIC_MAPPING[0][0]
        end_idx = end_index if end_index is not None else CYRILLIC_MAPPING[-1][0]
        mapping_to_process = [(idx, char) for idx, char in CYRILLIC_MAPPING if start_idx <= idx <= end_idx]

    print(f"\n🚀 Начинаем вставку {len(mapping_to_process)} символов...")
    print(f"Шрифт: {font_path}")
    print(f"Размер для заглавных: {FONT_SIZE_UPPER}px, для строчных: {FONT_SIZE_LOWER}px")
    print("-" * 60)

    success_count = 0
    for glyph_index, char in mapping_to_process:
        try:
            if insert_single_glyph(data, glyph_index, char, font_path, preview_mode):
                success_count += 1
            else:
                print(f"✗ Ошибка при вставке '{char}' в индекс {glyph_index}")
        except Exception as e:
            print(f"✗ Исключение при обработке '{char}' (индекс {glyph_index}): {e}")

    # Записываем изменения
    if success_count > 0:
        with open(nftr_file, 'wb') as f:
            f.write(data)
        
        print("-" * 60)
        print(f"✅ Успешно обработано: {success_count}/{len(mapping_to_process)} символов")
        print(f"Файл {nftr_file} обновлен!")
        print(f"⚠️  Не забудьте настроить ширины глифов в NFTRedit.exe")
        return True
    else:
        print("❌ Ни одного символа не было вставлено.")
        return False

def main():
    if len(sys.argv) < 2:
        print(f"Использование:")
        print(f"  python {sys.argv[0]} <файл.nftr> [шрифт] [начальный_индекс] [конечный_индекс] [--preview]")
        print(f"")
        print(f"Примеры:")
        print(f"  python {sys.argv[0]} tumefont-rus.nftr")
        print(f"  python {sys.argv[0]} tumefont-rus.nftr fonts/PressStart2P-Regular.ttf")
        print(f"  python {sys.argv[0]} tumefont-rus.nftr fonts/PressStart2P-Regular.ttf 32 40")
        print(f"  python {sys.argv[0]} tumefont-rus.nftr fonts/PressStart2P-Regular.ttf 32 40 --preview")
        print(f"")
        print(f"Параметры:")
        print(f"  --preview    Показывать превью каждого битмапа")
        print(f"")
        print(f"Диапазоны:")
        print(f"  Заглавные: индексы 32-64 (А-Я)")
        print(f"  Строчные:  индексы 65-97 (а-я)")
        sys.exit(1)

    nftr_file = sys.argv[1]
    font_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') and not sys.argv[2].isdigit() else FONT_PATH
    
    # Парсим аргументы
    start_index = None
    end_index = None
    preview_mode = False
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == '--preview':
            preview_mode = True
        elif arg.isdigit():
            if start_index is None:
                start_index = int(arg)
            elif end_index is None:
                end_index = int(arg)

    print(f"📝 Массовая вставка русских букв в NFTR")
    print(f"Файл: {nftr_file}")
    print(f"Шрифт: {font_path}")
    if start_index is not None:
        print(f"Диапазон: {start_index}-{end_index if end_index else 'конец'}")
    if preview_mode:
        print("Режим: показ превью")

    success = batch_insert_cyrillic(nftr_file, font_path, start_index, end_index, preview_mode)
    
    if success:
        print(f"\n🎉 Готово! Проверить результат можно командами:")
        print(f"python nftr_glyph_viewer.py {nftr_file} 32  # Буква А")
        print(f"python nftr_glyph_viewer.py {nftr_file} 65  # Буква а")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()