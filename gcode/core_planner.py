# gui/core_planner.py
import math
import re

class CNCPlannerX:
    def __init__(self, accel=150.0, min_speed=2.0, junction_deviation=0.02):
        self.accel = accel                     # мм/сек^2
        self.min_speed = min_speed             # мм/сек
        self.junction_deviation = junction_deviation  # мм

    def parse_and_plan(self, gcode_lines):
        """Главный публичный API метод."""
        # 1. Линеаризация (Чистый парсинг)
        segments = self._parse_to_segments(gcode_lines)
        if not segments:
            return []

        # 2. Математика Look-Ahead (Разгон / Торможение / Изломы)
        segments = self._apply_look_ahead(segments)
        
        # 3. Сборка бинарного потока пакетов B:... с 7 разделителями
        packet_stream = []
        for seg in segments:
            packet = (
                f"B:{seg['type']};{seg['line']};"
                f"{seg['x']:.3f};{seg['y']:.3f};{seg['z']:.3f};"
                f"{seg['f_min']:.3f};{seg['v_start']:.3f};{seg['v_end']:.3f}"
            )
            packet_stream.append(packet)
            
        return packet_stream

    def _parse_to_segments(self, gcode_lines):
        """Парсер модальных осей. Защищен от синтаксических ошибок."""
        segments = []
        curr_x, curr_y, curr_z = 0.0, 0.0, 0.0
        curr_f = 600.0  # мм/мин
        
        for idx, line in enumerate(gcode_lines):
            # 1. Переводим в верхний регистр и убираем пробелы по краям
            line_upper = line.upper().strip()
            if not line_upper:
                continue
                
            # 2. ИСПРАВЛЕНО: Безопасно отсекаем комментарии (split возвращает список, берем элемент)
            clean_line = line_upper.split(';')[0].strip()
            if not clean_line:
                continue
                
            # Поиск токенов через Regex
            g_match = re.search(r'G([0-1])', clean_line)
            m_match = re.search(r'M([0-9]+)', clean_line)
            x_match = re.search(r'X([-+]?[0-9]*\.?[0-9]+)', clean_line)
            y_match = re.search(r'Y([-+]?[0-9]*\.?[0-9]+)', clean_line)
            z_match = re.search(r'Z([-+]?[0-9]*\.?[0-9]+)', clean_line)
            f_match = re.search(r'F([0-9]*\.?[0-9]+)', clean_line)
            
            seg_type = 1  # По умолчанию движение G0/G1
            if m_match:
                seg_type = 3  # М-команда
                
            if f_match:
                curr_f = float(f_match.group(1))
            f_min = curr_f / 60.0  # Ограничение кадра (мм/сек)
            
            # Модальное автозаполнение осей (Защита от улета в 0)
            target_x = float(x_match.group(1)) if x_match else curr_x
            target_y = float(y_match.group(1)) if y_match else curr_y
            target_z = float(z_match.group(1)) if z_match else curr_z
            
            # Расчет дельт перемещений
            dx = target_x - curr_x
            dy = target_y - curr_y
            dz = target_z - curr_z
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Сохраняем абсолютно все кадры
            segment = {
                "type": seg_type, 
                "line": idx, 
                "x": target_x, "y": target_y, "z": target_z,
                "dx": dx, "dy": dy, "dz": dz, "length": length,
                "f_min": f_min, 
                "v_start": self.min_speed, 
                "v_end": self.min_speed
            }
            segments.append(segment)
            
            # Сдвигаем точку виртуального инструмента
            curr_x, curr_y, curr_z = target_x, target_y, target_z
            
        return segments

    def _apply_look_ahead(self, segments):
        """Классический трехпроходной Look-Ahead алгоритм ЧПУ."""
        if len(segments) <= 1:
            return segments
            
        # Инициализируем стыки максимальным маршевым потолком кадра
        for seg in segments:
            if seg["type"] == 1 and seg["length"] > 1e-4:
                seg["v_start"] = seg["f_min"]
                seg["v_end"] = seg["f_min"]
            else:
                seg["v_start"] = self.min_speed
                seg["v_end"] = self.min_speed
     
        # Пасс 1: Расчет лимитов скоростей на изломах векторов (Junction Deviation)
        for i in range(len(segments) - 1):
            seg = segments[i]
            next_seg = segments[i + 1]

            if seg["type"] != 1 or next_seg["type"] != 1 or seg["length"] < 1e-4 or next_seg["length"] < 1e-4:
                v_junction = self.min_speed
            else:
                dot_product = (seg["dx"] * next_seg["dx"] + seg["dy"] * next_seg["dy"] + seg["dz"] * next_seg["dz"])
                cos_vector = max(-1.0, min(1.0, dot_product / (seg["length"] * next_seg["length"])))
                
                # Каноничная инверсия знака угла для GRBL/Marlin геометрии
                junction_cos_theta = -cos_vector

                if junction_cos_theta > 0.99999:
                    v_junction = self.min_speed
                elif junction_cos_theta < -0.99999:
                    v_junction = min(seg["f_min"], next_seg["f_min"])
                else:
                    # Находим синус половины угла излома через формулу половинного угла
                    sin_half_theta = math.sqrt((1.0 - junction_cos_theta) / 2.0)
                    
                    # Расчет радиуса виртуальной окружности Junction Deviation
                    radius = (self.junction_deviation * sin_half_theta) / (1.0 - sin_half_theta)
                    
                    # Безопасная скорость прохождения угла
                    v_junction = math.sqrt(self.accel * radius)
                    v_junction = min(v_junction, seg["f_min"], next_seg["f_min"])
                    v_junction = max(v_junction, self.min_speed)

            seg["v_end"] = min(seg["v_end"], v_junction)
            next_seg["v_start"] = min(next_seg["v_start"], v_junction)

        # Фиксируем края всей программы (Оставляем как было)
        segments[0]["v_start"] = self.min_speed
        segments[-1]["v_end"] = self.min_speed

        
        # Пасс 2: Торможение (Обратный проход)
        for i in reversed(range(len(segments) - 1)):
            seg = segments[i]
            next_seg = segments[i + 1]
            
            if seg["type"] == 1 and seg["length"] > 1e-4:
                v_allowable = math.sqrt(seg["v_end"]**2 + 2.0 * self.accel * seg["length"])
                if seg["v_start"] > v_allowable:
                    seg["v_start"] = v_allowable
            
            if next_seg["length"] > 1e-4:
                # Волна торможения катится назад, но она МОЖЕТ ТОЛЬКО ЗАНИЖАТЬ 
                # конечную скорость текущего кадра, если будущий угол требует торможения
                seg["v_end"] = min(seg["v_end"], next_seg["v_start"])
            
        # Пасс 3: Разгон (Прямой проход)
        for i in range(len(segments) - 1):
            seg = segments[i]
            next_seg = segments[i + 1]
            
            if seg["type"] == 1 and seg["length"] > 1e-4:
                v_allowable = math.sqrt(seg["v_start"]**2 + 2.0 * self.accel * seg["length"])
                if seg["v_end"] > v_allowable:
                    seg["v_end"] = v_allowable
                    
            if seg["length"] > 1e-4:
                # Волна разгона катится вперед, но она МОЖЕТ ТОЛЬКО ЗАНИЖАТЬ 
                # начальную скорость следующего кадра, если текущий кадр не успел разогнаться
                next_seg["v_start"] = min(next_seg["v_start"], seg["v_end"])
            
        # Финальная инспекция нижнего порога скорости
        for seg in segments:
            if seg["type"] == 1 and seg["length"] > 1e-4:
                seg["v_start"] = max(seg["v_start"], self.min_speed)
                seg["v_end"] = max(seg["v_end"], self.min_speed)
                
        return segments
