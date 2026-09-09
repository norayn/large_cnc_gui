import math
import re

class ddCNCPlannerX:
    def __init__(self, accel=150.0, min_speed=2.0, junction_deviation=0.02):
        self.accel = accel                     # Ускорение (мм/сек^2)
        self.min_speed = min_speed             # Стартовая скорость (мм/сек)
        self.junction_deviation = junction_deviation  # Жесткость станины (мм)

    def parse_and_plan(self, gcode_lines):
        """
        Главный метод управления пайплайном подготовки программы.
        Вход: массив текстовых строк G-кода.
        Выход: массив скомпилированных бинарных пакетов B:... для ESP32.
        """
        # 1. Шаг парсинга: превращаем текст в массив геометрических отрезков
        segments = self._parse_to_segments(gcode_lines)
        
        # 2. Шаг математики Look-Ahead: рассчитываем безопасные скорости сопряжения на углах
        segments = self._apply_look_ahead(segments)
        
        # 3. Шаг бинаризации: сборка пакетов по вашему новому протоколу
        packet_stream = []
        for seg in segments:
            # Формируем структуру: B:TYPE;LINE_NUM;X;Y;Z;F_MAX;V_START;V_END
            # Округляем до 3 знаков после запятой для высокой точности
            packet = (
                f"B:{seg['type']};{seg['line']};"
                f"{seg['x']:.3f};{seg['y']:.3f};{seg['z']:.3f};"
                f"{seg['f_min']:.3f};{seg['v_start']:.3f};{seg['v_end']:.3f}"
            )
            packet_stream.append(packet)
            
        return packet_stream

    def _parse_to_segments(self, gcode_lines):
        """
        БЛОК 1: Инициализация структуры данных и модального кэша траектории
        """
        segments = []  # Итоговый массив геометрических сегментов
        
        # Виртуальный начальный ноль траектории (база отсчета)
        curr_x = 0.0
        curr_y = 0.0
        curr_z = 0.0
        
        # Модальная скорость подачи по умолчанию (мм/мин)
        curr_f = 600.0 
        # ==========================================
        # БЛОК 2: Построчный цикл и очистка от мусора
        # ==========================================
        for idx, line in enumerate(gcode_lines):
            # 1. Удаляем пробелы по краям, бьем по комментарию ';' и берем левую часть
            line = line.strip().split(';')[0].upper()
            
            # 2. Если после очистки комментариев строка пустая — пропускаем её
            if not line:
                continue
            # ==========================================
            # БЛОК 3: Извлечение токенов через Regex
            # ==========================================
            # Выдергиваем типы команд (G0/G1 или M)
            g_match = re.search(r'G([0-1])', line)
            m_match = re.search(r'M([0-9]+)', line)
            
            # Выдергиваем числовые значения осей и подачи
            x_match = re.search(r'X([-+]?[0-9]*\.?[0-9]+)', line)
            y_match = re.search(r'Y([-+]?[0-9]*\.?[0-9]+)', line)
            z_match = re.search(r'Z([-+]?[0-9]*\.?[0-9]+)', line)
            f_match = re.search(r'F([0-9]*\.?[0-9]+)', line)
            # --------------------------------------------------------
            # БЛОК 4 (Пункты 1-3): Типизация, модальный кэш F и осей X/Y/Z
            # --------------------------------------------------------
            # Пункт 1: Привязка оригинального номера кадра и базовый тип
            line_num = idx
            seg_type = 1  # По умолчанию 1 = интерполированное движение (G0/G1)
            if m_match:
                seg_type = 3  # 3 = вспомогательная M-команда (СОЖ, шпиндель)
            
            # Пункт 2: Модальное обновление скорости подачи (перевод мм/мин -> мм/сек)
            if f_match:
                curr_f = float(f_match.group(1))
            f_min = curr_f / 60.0  # Ограничение скорости для Look-Ahead
            
            # Пункт 3: Защита от улета в 0. Автозаполнение пропущенных координат
            target_x = float(x_match.group(1)) if x_match else curr_x
            target_y = float(y_match.group(1)) if y_match else curr_y
            target_z = float(z_match.group(1)) if z_match else curr_z
            # --------------------------------------------------------
            # БЛОК 4 (Пункты 4-5): Расчет 3D-геометрии и упаковка
            # --------------------------------------------------------
            # Пункт 4: Расчет дельт перемещений по осям X, Y, Z
            dx = target_x - curr_x
            dy = target_y - curr_y
            dz = target_z - curr_z
            
            # Длина вектора перемещения в пространстве по теореме Пифагора
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Пункт 5: Формирование структуры сегмента и сохранение
            segment = {
                "type": seg_type,
                "line": line_num,
                "x": target_x,
                "y": target_y,
                "z": target_z,
                "dx": dx,
                "dy": dy,
                "dz": dz,
                "length": length,
                "f_min": f_min,          # Максимальный предел скорости кадра (мм/сек)
                "v_start": self.min_speed, # Стартовая скорость (заглушка для Look-Ahead)
                "v_end": self.min_speed    # Конечная скорость (заглушка для Look-Ahead)
            }
            segments.append(segment)
            
            # Сдвигаем кэш позиций — целевая точка становится текущей для следующего кадра
            curr_x = target_x
            curr_y = target_y
            curr_z = target_z
            
        return segments # Возвращаем полностью готовый массив геометрических отрезков

    def _apply_look_ahead(self, segments):
        """
        БЛОК 1: Инициализация граничных условий Look-Ahead планировщика
        """
        # Если сегментов нет или их слишком мало, математический расчет не требуется
        if len(segments) <= 1:
            return segments
            
        # Задаем граничные условия для краев программы ЧПУ
        # Первый кадр начинает движение со стартовой скорости
        segments[0]['v_start'] = self.min_speed
        
        # Последний кадр завершает программу полной остановкой
        segments[-1]['v_end'] = self.min_speed
        # ==========================================================
        # БЛОК 2: Попарный анализ углов излома (Junction Deviation)
        # ==========================================================
        for i in range(len(segments) - 1):
            seg = segments[i]
            next_seg = segments[i + 1]
            
            # Если хотя бы один из сегментов не движение (например, М-команда) — гасим скорость на стыке
            if seg["type"] != 1 or next_seg["type"] != 1:
                v_junction = self.min_speed
            else:
                # Проверка на нулевую длину векторов, чтобы избежать деления на ноль
                if seg["length"] < 1e-4 or next_seg["length"] < 1e-4:
                    v_junction = self.min_speed
                else:
                    # 1. Скалярное произведение векторов в 3D
                    dot_product = (seg["dx"] * next_seg["dx"] + 
                                   seg["dy"] * next_seg["dy"] + 
                                   seg["dz"] * next_seg["dz"])
                    
                    # 2. Находим косинус угла излома траектории
                    cos_theta = dot_product / (seg["length"] * next_seg["length"])
                    cos_theta = max(-1.0, min(1.0, cos_theta)) # Ограничение диапазона [-1, 1]
                    
                    # Если векторы сонаправлены (прямая линия, угол 0, косинус 1) — тормозить не нужно
                    if cos_theta > 0.999999:
                        v_junction = min(seg["f_min"], next_seg["f_min"])
                    else:
                        # 3. Вычисление синуса половинного угла по тригонометрическому тождеству
                        sin_half_theta = math.sqrt((1.0 - cos_theta) / 2.0)
                        
                        # 4. Расчет виртуального радиуса скругления угла по формуле Junction Deviation
                        radius = (self.junction_deviation * sin_half_theta) / (1.0 - sin_half_theta)
                        
                        # 5. Центростремительный лимит скорости прохождения угла по вашему ТЗ
                        v_junction = math.sqrt(self.accel * radius)
                        
                        # Ограничиваем скорость возможностями моторов текущего и следующего кадра
                        v_junction = min(v_junction, seg["f_min"], next_seg["f_min"])
                        v_junction = max(v_junction, self.min_speed)

            # Синхронизируем стык: конец текущего кадра равен началу следующего кадра
            seg["v_end"] = v_junction
            next_seg["v_start"] = v_junction
        # ==========================================================
        # БЛОК 3: Обратный проход Look-Ahead (Расчет волны торможения)
        # ==========================================================
        # Идем от предпоследнего сегмента назад до самого первого
        for i in reversed(range(len(segments) - 1)):
            seg = segments[i]
            next_seg = segments[i + 1]
            
            # Просчитываем торможение только для физических векторов перемещения
            if seg["type"] == 1:
                # На основе длины вектора и скорости на его конце вычисляем
                # максимально допустимую скорость на входе в этот кадр
                v_allowable = math.sqrt(seg["v_end"]**2 + 2.0 * self.accel * seg["length"])
                
                # Если скорость входа превышает физический лимит торможения — зажимаем её
                if seg["v_start"] > v_allowable:
                    seg["v_start"] = v_allowable
                    
                # Гарантируем, что скорость входа не прыгнет выше маршевого потолка F кадра
                seg["v_start"] = min(seg["v_start"], seg["f_min"])
            
            # Накатываем волну торможения назад: 
            # новое скорректированное начало следующего кадра становится концом текущего
            seg["v_end"] = next_seg["v_start"]
        # ==========================================================
        # БЛОК 4: Прямой проход Look-Ahead (Расчет волны разгона)
        # ==========================================================
        # Идем от самого первого сегмента вперед до конца программы
        for i in range(len(segments) - 1):
            seg = segments[i]
            next_seg = segments[i + 1]
            
            if seg["type"] == 1:
                # На основе стартовой скорости и длины вектора вычисляем
                # физически достижимую скорость на выходе из этого кадра
                v_allowable = math.sqrt(seg["v_start"]**2 + 2.0 * self.accel * seg["length"])
                
                # If скорость выхода превышает возможности разгона — зажимаем её
                if seg["v_end"] > v_allowable:
                    seg["v_end"] = v_allowable
                    
                # Гарантируем, что скорость выхода не превышает маршевый потолок F кадра
                seg["v_end"] = min(seg["v_end"], seg["f_min"])
            
            # Накатываем волну разгона вперед:
            # скорректированный конец текущего кадра становится началом следующего
            next_seg["v_start"] = seg["v_end"]
            
        return segments # Возвращаем полностью просчитанный массив траекторий
