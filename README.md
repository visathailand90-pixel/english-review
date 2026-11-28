# English Apps
Существующие приложения на прежних адресах:
- Повторение: https://visathailand90-pixel.github.io/english-review/
- Домашняя работа 14: https://visathailand90-pixel.github.io/english-review/#homework14
- Предыдущая домашняя работа 13: https://visathailand90-pixel.github.io/english-review/#homework13
- Слова: https://visathailand90-pixel.github.io/english-review/words/
- Читалка: https://visathailand90-pixel.github.io/english-review/reader/

Закрытые упражнения, словарь и готовая читалка работают без API и входа. Дополнительный AI опционален и ограничен существующей серверной защитой/сроком. Неизвестные свободные варианты остаются без оценки; эталоны и пояснения доступны.

Источники: app-template.html, lesson-data/*.json; words/bank.json и исходные PACK1/PACK2 в words/index.html; reader/index.html и reader/texts.json. python tools/build.py создаёт index.html, bank.js, texts.js, context.js и версию кеша. Сгенерированные файлы не редактировать вместо источников.

Прогресс хранится в localStorage конкретного браузера (english-review:v4, chitalka.*, старые pack keys, verbs:*). Публикация его не переносит; используйте отдельный JSON-экспорт/импорт каждого приложения. Не удалять данные. Service worker обеспечивает повторный запуск offline после первого HTTPS-посещения.

Проверки: tools/test_apps.py, validate.py, test_upgrade.py, test_smart.py, test_lesson12.py, test_lesson13.py, test_offline.py, test_lesson14.py и node tools/test_backend.mjs. Публикация только по поручению через publish-english.ps1 с точным списком -Files, без blanket staging и force push. Секреты и личные исходники не коммитить.

Для локального агента полный вход и передача находятся в ../00_READ_FIRST.md, ../AGENTS.md и документах 01–08; инструкция этого клона — AGENTS.md. Если передан только публичный репозиторий без локальной документации, не выдумывать личный контекст или прогресс.

Урок 14: вопросы, маршруты и причины опоздания;20 разделов теории,166 основных и 75 домашних упражнений,15 домашних выражений,35 новых слов +11 повторов. Три новых оригинальных текста A2 доступны сразу, библиотека содержит 7 готовых текстов. Личные документы Gemini не публикуются.

В уроке 14 stand, lose, cut, fall — ссылки на уже существующие irregularVerbs/pastVerbs, обозначенные entryType:reference и canonicalRef внутри контекстной карточки. Их позиции сохранены; это повторение, не новые канонические записи. Остальные ссылки wordRefs работают по прежнему контракту.
