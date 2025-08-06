#!/usr/bin/env python3
"""
Скрипт для вставки битмапа кириллической буквы в файл NFTR
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
FONT_SIZE = 12  # Увеличили размер шрифта
BITMAP_WIDTH = 13
BITMAP_HEIGHT = 15

def generate_char_bitmap(char, font_path, font_size, width, height):
    """
    Генерирует битмап символа и возвращает его как список пикселей (0 или 1)
    с учетом специальной схемы отображения NFTR
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

def test_pixel_mapping():
    """
    Тестовая функция для понимания схемы отображения NFTR
    """
    print("Тест соответствия пикселей:")
    print("Отображение -> Данные")
    
    for display_y in range(CELL_HEIGHT):
        print(f"\nСтрока отображения {display_y}:")
        
        # Столбцы 8-12 из строки данных display_y (показываются в позициях 0-4 отображения)
        for i, data_x in enumerate(range(8, 13)):
            print(f"  Отображение({i}, {display_y}) <- Данные({data_x}, {display_y})")
        
        # Столбцы 0-7 из строки данных display_y+1 (показываются в позициях 5-12 отображения)  
        if display_y < CELL_HEIGHT - 1:
            for i, data_x in enumerate(range(0, 8)):
                display_x = i + 5
                data_y = display_y + 1
                print(f"  Отображение({display_x}, {display_y}) <- Данные({data_x}, {data_y})")
        else:
            for i in range(8):
                display_x = i + 5
                print(f"  Отображение({display_x}, {display_y}) <- Пусто")

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

def preview_bitmap(pixels):
    """
    Показывает превью битмапа в консоли
    """
    print("Превью битмапа:")
    print("+" + "-" * (CELL_WIDTH * 2) + "+")
    
    for y in range(CELL_HEIGHT):
        print("|", end="")
        for x in range(CELL_WIDTH):
            idx = y * CELL_WIDTH + x
            if idx < len(pixels):
                print("██" if pixels[idx] else "  ", end="")
        print("|")
    
    print("+" + "-" * (CELL_WIDTH * 2) + "+")

def insert_glyph(nftr_file, glyph_index, char, font_path=FONT_PATH):
    """
    Вставляет ТОЛЬКО битмап символа в файл NFTR (без изменения ширины и других данных)
    """
    if not os.path.exists(nftr_file):
        print(f"ОШИБКА: Файл '{nftr_file}' не найден.")
        return False

    if not (0 <= glyph_index < NUM_GLYPHS):
        print(f"ОШИБКА: Индекс должен быть в диапазоне от 0 до {NUM_GLYPHS - 1}.")
        return False

    # Генерируем битмап
    pixels, actual_width = generate_char_bitmap(char, font_path, FONT_SIZE, BITMAP_WIDTH, BITMAP_HEIGHT)
    if pixels is None:
        return False

    print(f"Генерируем битмап для символа '{char}'")
    print(f"Фактическая ширина: {actual_width} пикселей (НЕ записывается в файл)")
    
    # Показываем превью
    preview_bitmap(pixels)

    # Преобразуем в байты
    bitmap_bytes = pixels_to_nftr_bytes(pixels)
    if bitmap_bytes is None:
        return False

    # Читаем файл
    with open(nftr_file, 'rb') as f:
        data = bytearray(f.read())

    # Вычисляем только адрес битмапа
    bitmap_addr = CGLP_OFFSET + (glyph_index * BYTES_PER_GLYPH_BITMAP)

    print(f"\nВставляем ТОЛЬКО битмап в файл:")
    print(f"Индекс глифа: {glyph_index}")
    print(f"Адрес битмапа: {bitmap_addr} (0x{bitmap_addr:X})")

    # Проверяем границы
    if bitmap_addr + BYTES_PER_GLYPH_BITMAP > len(data):
        print(f"ОШИБКА: Адрес битмапа ({bitmap_addr}) выходит за границы файла ({len(data)})")
        return False

    # Создаем резервную копию
    backup_file = nftr_file + '.backup'
    if not os.path.exists(backup_file):
        with open(backup_file, 'wb') as f:
            with open(nftr_file, 'rb') as orig:
                f.write(orig.read())
        print(f"Создана резервная копия: {backup_file}")

    # Записываем ТОЛЬКО битмап
    for i, byte_val in enumerate(bitmap_bytes):
        data[bitmap_addr + i] = byte_val
    print(f"Записано {len(bitmap_bytes)} байт битмапа")
    print("ВНИМАНИЕ: Ширина глифа НЕ изменена - настройте её в NFTRedit.exe")

    # Записываем изменения
    with open(nftr_file, 'wb') as f:
        f.write(data)
    
    print(f"Файл {nftr_file} успешно обновлен!")
    return True

def main():
    if len(sys.argv) < 4:
        print(f"Использование: python {sys.argv[0]} <файл.nftr> <индекс_глифа> <символ> [путь_к_шрифту]")
        print("Пример: python insert_cyrillic_glyph.py tumefont-rus.nftr 32 А")
        print("Для тестирования схемы отображения: python insert_cyrillic_glyph.py test")
        sys.exit(1)

    if sys.argv[1] == "test":
        test_pixel_mapping()
        return

    nftr_file = sys.argv[1]
    
    try:
        glyph_index = int(sys.argv[2])
    except ValueError:
        print(f"ОШИБКА: Индекс '{sys.argv[2]}' не является целым числом.")
        sys.exit(1)

    char = sys.argv[3]
    font_path = sys.argv[4] if len(sys.argv) > 4 else FONT_PATH

    success = insert_glyph(nftr_file, glyph_index, char, font_path)
    if success:
        print(f"\n✓ Битмап символа '{char}' успешно вставлен в индекс {glyph_index}")
        print(f"⚠️  ВАЖНО: Не забудьте настроить ширину глифа в NFTRedit.exe")
        print(f"Проверить битмап можно командой:")
        print(f"python nftr_glyph_viewer.py {nftr_file} {glyph_index}")
    else:
        print("\n✗ Произошла ошибка при вставке битмапа")
        sys.exit(1)

if __name__ == "__main__":
    main()