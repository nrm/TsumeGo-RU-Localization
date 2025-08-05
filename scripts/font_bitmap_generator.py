from PIL import Image, ImageDraw, ImageFont

def render_char_to_console(char, font_path, font_size, width, height):
    """
    Рендерит символ в виде битмапа с рамкой, нумерацией строк и столбцов,
    и точками на фоне. Рассчитывает фактическую ширину символа.
    """
    # Создание холста и загрузка шрифта
    image = Image.new('L', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"ОШИБКА: Шрифт не найден по пути: {font_path}")
        return

    # Центрирование и отрисовка символа
    try:
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(char, font=font)
        
    x_pos_draw = (width - text_width) / 2
    y_pos_draw = (height - text_height) / 2 - 1
    draw.text((x_pos_draw, y_pos_draw), char, font=font, fill='black')

    # Расчет фактической ширины
    min_x, max_x = width, -1
    for y in range(height):
        for x in range(width):
            if image.getpixel((x, y)) < 128:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
    actual_width = (max_x - min_x + 1) if max_x != -1 else 0

    # --- ВЫВОД В КОНСОЛЬ С НУМЕРАЦИЕЙ ---
    print(f"--- Символ: '{char}' | Факт. ширина: {actual_width}px ---")
    
    # Нумерация столбцов (сверху)
    col_tens = "   " + "".join(['1' if i >= 10 else ' ' for i in range(width)])
    col_units = "   " + "".join([str(i % 10) for i in range(width)])
    print(col_tens)
    print(col_units)

    # Верхняя рамка
    print(f"  +{'-' * width}+")

    # Строки с нумерацией
    for y in range(height):
        line = "".join(["█" if image.getpixel((x, y)) < 128 else "·" for x in range(width)])
        # f"{y:2d}" форматирует число, чтобы оно всегда занимало 2 символа ( " 0", " 1", ..., "14")
        print(f"{y:2d}|{line}|")

    # Нижняя рамка
    print(f"  +{'-' * width}+")
    print()  # Пустая строка для разделения


if __name__ == '__main__':
    # --- ОСНОВНЫЕ ПАРАМЕТРЫ ---
    FONT_PATH = "fonts/PressStart2P-Regular.ttf"
    # FONT_PATH = "OpenSans-VariableFont_wdth,wght.ttf"
    # FONT_PATH = "cyrillic_pixel-7.ttf"
    FONT_SIZE = 8
    BITMAP_WIDTH = 13
    BITMAP_HEIGHT = 15
    
    uppercase_cyrillic = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    lowercase_cyrillic = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

    for u_char, l_char in zip(uppercase_cyrillic, lowercase_cyrillic):
        render_char_to_console(u_char, FONT_PATH, FONT_SIZE, BITMAP_WIDTH, BITMAP_HEIGHT)
        render_char_to_console(l_char, FONT_PATH, FONT_SIZE, BITMAP_WIDTH, BITMAP_HEIGHT)
