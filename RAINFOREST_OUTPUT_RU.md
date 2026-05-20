# Лист Output для RainForest — Итоговый отчёт

**Дата:** 5 мая 2026  
**Статус:** ✓ Завершено

## Что было выполнено

### 1. ✓ Заполнен лист Output в variables_schema.xlsx

Собрано **36 датчиков климатического состояния RainForest**:
- **18 датчиков температуры** (T(x,t), AirTempC)
- **18 датчиков влажности** (RH(x,t))
- **4 вертикальные мачты**: Mountain, Northeast, Northwest, South
- **Высоты**: 100, 300, 700, 1300 см на каждой мачте (некоторые + 2000 см)

### 2. ✓ Создан автоматический генератор

**Файл:** `scripts/update_rainforest_output_sheet.py`

**Использование:**
```bash
cd /home/dimitri/PycharmProjects/CO2Flux
python3 scripts/update_rainforest_output_sheet.py
```

**Что делает:**
- Читает `Bio2-Rainforest-Inventory.xlsx`
- Фильтрует только климатические переменные (Температура, Влажность)
- Автоматически генерирует SQL-запросы для каждого датчика
- Заполняет все 37 колонок метаданными
- Сохраняет вертикальную структуру мачт

### 3. ✓ Создана документация

**Файлы:**
- `Sensors_Description/output_sheet_notes.md` — полное описание структуры Output листа
- `RAINFOREST_OUTPUT_SETUP_REPORT.md` — англоязычный отчёт
- Обновлён `AGENTS.md` — инструкции для AI-агентов

## Структура Output листа

Каждая строка = один датчик = один временной ряд  
Всего: **36 строк данных** + заголовок

### Пример первого датчика (температура, Mountain Tower, 100 см):

```
Переменная физическая:       Air temperature
Символ:                      T(x,t)
Z-координата [м]:            1.0              ← 100 см = 1.0 м
Роль в PDE:                  Pointwise state value constraint
Источник:                    RainForest SensorDB inventory
Сенсор Oracle ID:            96
Код датчика:                 TRF_MTN_100_HMP45
Таблица Oracle:              BIOMS.DATAVALUES
Oracle selector:             dv.sensorid = 96 AND dv.variableid = 16
Единицы:                     degC
Локация:                     TRF Mountain Tower
SQL-запрос (готовый):        SELECT dv.LOCALDATETIME, dv.DATAVALUE 
                             FROM bioms.DATAVALUES dv
                             WHERE dv.sensorid = 96 AND dv.variableid = 16
                             ORDER BY dv.LOCALDATETIME
```

## Таблица датчиков

```
Мачта                     Температура     Влажность      Всего
─────────────────────────────────────────────────────────────
Mountain Tower            4 датчика        4 датчика      8
Northeast Tower           5 датчиков       5 датчиков     10
Northwest Tower           4 датчика        4 датчика      8
South Tower               5 датчиков       5 датчиков     10
─────────────────────────────────────────────────────────────
ИТОГО                     18 датчиков      18 датчиков    36
```

## Как использовать Output лист

### Извлечь данные конкретного датчика из Oracle:

Для любой строки Output используйте SQL из колонки AA, например:

```sql
SELECT dv.LOCALDATETIME, dv.DATAVALUE
FROM bioms.DATAVALUES dv
WHERE dv.sensorid = 96 AND dv.variableid = 16
ORDER BY dv.LOCALDATETIME;
```

### Понимание связи Input → Output:

**Input лист** содержит команды управления (например, скорость вентилятора)  
**Output лист** содержит результаты измерений (количество влаги в воздухе)

Когда вы меняете Input (команду оборудованию), Output датчики показывают, произошло ли ожидаемое изменение климата.

## Следующие этапы

### Этап 1 (опционально): Валидация в Oracle
Если нужно — можно добавить в скрипт автоматическую проверку доступности каждого датчика в Oracle.

**Текущее состояние:** колонка AC показывает "validation pending"

### Этап 2 (запланирован): Mapping Input → Output

Создать таблицу связей:

| Input (команда) | Output (датчик) | Ожидаемый эффект | Примечание |
|---|---|---|---|
| MiscRF1_LowLndTmp (уставка) | TRF_MTN_100_HMP45 (T) | Т увеличится | Прямое управление |
| Вентилятор (скорость) | Все RH датчики | RH снизится | Обезвоживание |
| Дождевание (ирригация) | TRF_*_100 (T) | Т снизится | Испарительное охлаждение |

### Этап 3 (после mapping): Обратная задача

С установленными связями Input→Output можно:
1. Определить целевые значения климата
2. Найти оптимальные Input команды для достижения целей
3. Использовать Output датчики для калибровки и валидации модели

## Быстрые команды

### Обновить Output лист:
```bash
python3 scripts/update_rainforest_output_sheet.py
```

### Прочитать о структуре Output:
```
Читать: Sensors_Description/output_sheet_notes.md
```

### Прочитать правила расширения workbook:
```
Читать: Sensors_Description/variables_schema_notes.md
```

## Изменённые/созданные файлы

| Файл | Статус |
|------|--------|
| `variables_schema.xlsx` (Output sheet) | ✓ Заполнен 36 датчиками |
| `scripts/update_rainforest_output_sheet.py` | ✓ Создан |
| `Sensors_Description/output_sheet_notes.md` | ✓ Документация |
| `AGENTS.md` | ✓ Обновлён |

## Константы (для вашей справки)

**Oracle переменные для RainForest:**
- AirTempC (Температура): variable_id = 16
- RH (Влажность): variable_id = 15

**Oracle таблица:**
- BIOMS.DATAVALUES

**Мачты и высоты:**
- Mountain Tower: 100, 300, 700, 1300 см
- Northeast Tower: 100, 300, 700, 1300, 2000 см
- Northwest Tower: 100, 300, 700, 1300 см
- South Tower: 100, 300, 700, 1300, 2000 см

---

## ✓ Готово!

Output лист готов к использованию для:
1. Наблюдения климатического состояния RainForest
2. Проверки ответа структур на изменение Input управления
3. Калибровки и валидации моделей
4. Формулирования обратной задачи

