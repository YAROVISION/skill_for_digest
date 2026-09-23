# Skill: Manual Document Segmentation

**Target File**: Daijest_VKKS_01_02_2025

## Prompts Guidance
- Один сегмент = Одна справа = Один JSON.
- **ВАЖЛИВО**: До сегменту має входити теза, обставини справи та правовий висновок. Включайте також блоки "Подібні правові висновки" або "Аналогічний правовий висновок", якщо вони є наприкінці сегменту.
- **МЕТАДАНІ**: Для цього документа Номер справи (case_number), Дата рішення (date), Суд (court) та Посилання (url) знаходяться в кінці тексту, в абзаці, який починається з "Детальніше з текстом постанови...".
  - **case_number**: Витягніть номер справи з цього абзацу (наприклад, "9901/468/21" або "990/51/24").
  - **date**: Знайдіть дату рішення в цьому ж абзаці (наприклад, "07 листопада 2024 року" -> перетворіть у формат "2024-11-07").
  - **url**: Витягніть повне посилання з круглик дужок в кінці цього абзацу (наприклад, "https://reyestr.court.gov.ua/Review/123314000").
  - **court**: Визначте суд за абревіатурою (наприклад, "ВП ВС" -> "Велика Палата Верховного Суду", "КЦС ВС" -> "Касаційний цивільний суд у складі Верховного Суду", "КАС ВС" -> "Касаційний адміністративний суд у складі Верховного Суду", "КГС ВС" -> "Касаційний господарський суд у складі Верховного Суду").

## Segments

### [manual_a1]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.1. Щодо можливості оскарження до суду рішення ВККС про невідповідність судді
- **End**: (провадження № 11-132заі24) – за посиланням: https://reyestr.court.gov.ua/Review/123553839.

### [manual_a2]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.2. Щодо можливості оскарження до суду дій ВККС з продовження
- **End**: [https://reyestr.court.gov.ua/Review/120370729](https://reyestr.court.gov.ua/Review/120370729) .

### [manual_a3]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.3. Щодо визнання дискреційними повноважень ВККС стосовно кваліфікаційного
- **End**: за посиланням: https://reyestr.court.gov.ua/Review/118868396.

### [manual_a4]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.4. Щодо визнання повноважень ВККС за участю ГРМЕ вирішувати питання
- **End**: https://reyestr.court.gov.ua/Review/119168573.

### [manual_a5]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.5. Щодо визнання повноважень за членами ВККС оцінювати критерії професійної
- **End**: [https://reyestr.court.gov.ua/Review/89819782.](https://reyestr.court.gov.ua/Review/89819782)

### [manual_a6]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.6. Щодо визнання правомірною відмови ВККС у допуску кандидата на зайняття
- **End**: [https://reyestr.court.gov.ua/Review/95382816.](https://reyestr.court.gov.ua/Review/95382816)

### [manual_a7]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.7. Щодо визнання неправомірним рішення ВККС про відмову в допуску судді
- **End**: [https://reyestr.court.gov.ua/Review/124809043.](https://reyestr.court.gov.ua/Review/124809043)

### [manual_a8]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.8. Щодо визнання неправомірним рішення ВККС про відмову в допуску судді
- **End**: [https://reyestr.court.gov.ua/Review/117442775.](https://reyestr.court.gov.ua/Review/117442775)

### [manual_a9]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.9. Щодо правомірності призначення ВККС проведення комп’ютерного тестування
- **End**: [https://reyestr.court.gov.ua/Review/95242247.](https://reyestr.court.gov.ua/Review/95242247)

### [manual_a10]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.10. Щодо визнання правомірним рішення ВККС про призначення кваліфікаційного
- **End**: [https://reyestr.court.gov.ua/Review/113901763.](https://reyestr.court.gov.ua/Review/113901763)

### [manual_a11]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.11. Щодо відсутності підстав для визнання протиправним рішення ВККС про
- **End**: [https://reyestr.court.gov.ua/Review/96788086.](https://reyestr.court.gov.ua/Review/96788086)

### [manual_a12]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.12. Щодо повноважень ВККС здійснювати перегляд прийнятих палатою
- **End**: [https://reyestr.court.gov.ua/Review/89289952.](https://reyestr.court.gov.ua/Review/89289952)

### [manual_a13]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.13. Щодо необхідності ВККС належно мотивувати своє рішення про відмову
- **End**: [https://reyestr.court.gov.ua/Review/90458913.](https://reyestr.court.gov.ua/Review/90458913)

### [manual_a14]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.14. Щодо визнання внесених ВККС змін до пункту 14 розділу V
- **End**: [https://reyestr.court.gov.ua/Review/101302982.](https://reyestr.court.gov.ua/Review/101302982)

### [manual_a15]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.15. Щодо повноважень ВККС у пленарному складі вирішувати питання
- **End**: [(провадження № 11-1221заі19) – за посиланням: https://reyestr.court.gov.ua/Review/90458949.](https://reyestr.court.gov.ua/Review/90458949)

### [manual_a16]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.16. Щодо порядку набрання чинності рішенням ВККС у складі колегії про
- **End**: https://reyestr.court.gov.ua/Review/114423829.

### [manual_a17]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.17. Щодо повноважень колегій ВККС ухвалювати рішення про відповідність
- **End**: [https://reyestr.court.gov.ua/Review/120088917.](https://reyestr.court.gov.ua/Review/120088917)

### [manual_a18]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.18. Щодо неналежності до розгляду в порядку адміністративного судочинства
- **End**: [https://reyestr.court.gov.ua/Review/110208969.](https://reyestr.court.gov.ua/Review/110208969)

### [manual_a19]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.19. Щодо визнання правомірним рішення ВККС про призначення іспитів
- **End**: [https://reyestr.court.gov.ua/Review/96006361.](https://reyestr.court.gov.ua/Review/96006361)

### [manual_a20]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.20. Щодо відсутності підстав для визнання завершеним кваліфікаційного
- **End**: [https://reyestr.court.gov.ua/Review/105078717.](https://reyestr.court.gov.ua/Review/105078717)

### [manual_a21]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.21. Щодо неможливості оскарження до суду рішення колегії ВККС про винесення
- **End**: [https://reyestr.court.gov.ua/Review/120088910.](https://reyestr.court.gov.ua/Review/120088910)

### [manual_a22]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.22. Щодо визнання правомірними положень Регламенту про надання доступу
- **End**: [https://reyestr.court.gov.ua/Review/96377417.](https://reyestr.court.gov.ua/Review/96377417)

### [manual_a23]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.23. Щодо необхідності завершення процедури кваліфікаційного оцінювання судді,
- **End**: https://reyestr.court.gov.ua/Review/118465127.

### [manual_a24]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.24. Щодо відсутності підстав для визнання протиправним незавершення Комісією
- **End**: [https://reyestr.court.gov.ua/Review/124904873.](https://reyestr.court.gov.ua/Review/124904873)

### [manual_a25]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.25. Щодо строку на звернення до суду з позовом про визнання протиправним
- **End**: (провадження № 11-49заі24) – за посиланням: https://reyestr.court.gov.ua/Review/119168574.

### [manual_a26]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.26. Щодо визнання того, що зміна судової практики не є обставиною, яка впливає
- **End**: https://reyestr.court.gov.ua/Review/123086005 .

### [manual_a27]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.27. Щодо неналежності до компетенції суду розгляду позову про скасування
- **End**: (провадження № 11-154заі24) – за посиланням: https://reyestr.court.gov.ua/Review/122092396 .

### [manual_a28]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.28. Щодо неналежності до компетенції суду розгляду позову про скасування
- **End**: [https://reyestr.court.gov.ua/Review/118689106.](https://reyestr.court.gov.ua/Review/118689106)

### [manual_a29]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 1.29. Щодо можливості оскарження рішень (актів індивідуальної дії) ВККС про
- **End**: https://reyestr.court.gov.ua/Review/88138164.

### [manual_a30]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.1. Щодо повноважень ВККС ухвалити рішення про надання рекомендацій
- **End**: [https://reyestr.court.gov.ua/Review/96669463.](https://reyestr.court.gov.ua/Review/96669463)

### [manual_a31]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.2. Щодо визнання правомірним рішення ВККС про припинення участі кандидата
- **End**: [https://reyestr.court.gov.ua/Review/90458936.](https://reyestr.court.gov.ua/Review/90458936)

### [manual_a32]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.3. Щодо визнання правомірним рішення ВККС про відмову кандидату в допуску
- **End**: [https://reyestr.court.gov.ua/Review/119653577.](https://reyestr.court.gov.ua/Review/119653577)

### [manual_a33]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.4. Щодо визнання правомірним рішення ВККС про припинення участі кандидата
- **End**: https://reyestr.court.gov.ua/Review/123081968.

### [manual_a34]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.5. Щодо скасування рішень ВККС як необґрунтованих у частині визнання того,
- **End**: [https://reyestr.court.gov.ua/Review/119265162.](https://reyestr.court.gov.ua/Review/119265162)

### [manual_a35]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.6. Щодо визнання протиправним рішення ВККС про припинення участі позивача
- **End**: [https://reyestr.court.gov.ua/Review/86877099.](https://reyestr.court.gov.ua/Review/86877099)

### [manual_a36]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.7. Щодо визнання протиправним рішення ВККС про відмову в наданні
- **End**: [https://reyestr.court.gov.ua/Review/123992357](https://reyestr.court.gov.ua/Review/123992357) .

### [manual_a37]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.8. Щодо визнання протиправним рішення ВККС про відмову в наданні
- **End**: [https://reyestr.court.gov.ua/Review/123602975](https://reyestr.court.gov.ua/Review/123602975) .

### [manual_a38]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.9. Щодо визнання протиправним рішення ВККС про відмову в наданні
- **End**: [https://reyestr.court.gov.ua/Review/123081974](https://reyestr.court.gov.ua/Review/123081974) .

### [manual_a39]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.10. Щодо визнання протиправним рішення ВККС про відмову в наданні
- **End**: [https://reyestr.court.gov.ua/Review/123081970](https://reyestr.court.gov.ua/Review/123081970) .

### [manual_a40]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.11. Щодо відсутності підстав для визнання неправомірним рішення ВККС про
- **End**: [https://reyestr.court.gov.ua/Review/79413217.](https://reyestr.court.gov.ua/Review/79413217)

### [manual_a41]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.12. Щодо відсутності підстав для визнання протиправним рішення ВККС у частині
- **End**: [https://reyestr.court.gov.ua/Review/89903941](https://reyestr.court.gov.ua/Review/89903941) .

### [manual_a42]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.13. Щодо вимог, яким повинні відповідати особи, які претендують на допуск ВККС
- **End**: [(провадження № 11-531заі19) – за посиланням: https://reyestr.court.gov.ua/Review/85679206.](https://reyestr.court.gov.ua/Review/85679206)

### [manual_a43]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.14. Щодо визнання правомірним рішення ВККС про оголошення конкурсу
- **End**: [https://reyestr.court.gov.ua/Review/87985471.](https://reyestr.court.gov.ua/Review/87985471)

### [manual_a44]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.15. Щодо строку на звернення до суду з позовом про визнання протиправним
- **End**: [https://reyestr.court.gov.ua/Review/86401310.](https://reyestr.court.gov.ua/Review/86401310)

### [manual_a45]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 2.16. Щодо строку на звернення до суду з позовом про зобов’язання ВККС
- **End**: [https://reyestr.court.gov.ua/Review/99890775.](https://reyestr.court.gov.ua/Review/99890775)

### [manual_a46]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 3.1. Щодо оскарження рішення ВККС про відмову в допуску до участі в конкурсі
- **End**: [https://reyestr.court.gov.ua/Review/120426275.](https://reyestr.court.gov.ua/Review/120426275)

### [manual_a47]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 3.2. Щодо оскарження рішення ВККС про відмову в допуску до участі в конкурсі
- **End**: [https://reyestr.court.gov.ua/Review/123466972](https://reyestr.court.gov.ua/Review/123466972) .

### [manual_a48]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 3.3. Щодо оскарження рішення ВККС про відмову в допуску до участі в конкурсі
- **End**: [https://reyestr.court.gov.ua/Review/122603356.](https://reyestr.court.gov.ua/Review/122603356)

### [manual_a49]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 3.4. Щодо оскарження рішення ВККС про відмову в допуску до участі в конкурсі
- **End**: [https://reyestr.court.gov.ua/Review/123949439](https://reyestr.court.gov.ua/Review/123949439) .

### [manual_a50]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 3.5. Щодо оскарження рішення ВККС про відмову в допуску до участі в конкурсі
- **End**: [https://reyestr.court.gov.ua/Review/123081963](https://reyestr.court.gov.ua/Review/123081963) .

### [manual_a51]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 4.1. Щодо відсутності підстав для визнання протиправною бездіяльності ВККС про
- **End**: [(провадження № 11-1208заі18) – за посиланням: https://reyestr.court.gov.ua/Review/79684986.](https://reyestr.court.gov.ua/Review/79684986)

### [manual_a52]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 4.2. Щодо відсутності підстав для визнання протиправним ненадання ВККС
- **End**: [https://reyestr.court.gov.ua/Review/119454174](https://reyestr.court.gov.ua/Review/119454174) .

### [manual_a53]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 4.3. Щодо відсутності підстав для визнання протиправною бездіяльності ВККС
- **End**: https://reyestr.court.gov.ua/Review/122957407.

### [manual_a54]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 4.4. Щодо допустимості оскарження рішення ВККС стосовно надання рекомендації
- **End**: [(провадження № 11-1523заі18) – за посиланням: https://reyestr.court.gov.ua/Review/82308642.](https://reyestr.court.gov.ua/Review/82308642)

### [manual_a55]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.1. Щодо відсутності підстав для визнання протиправним неприйняття ВККС
- **End**: [https://reyestr.court.gov.ua/Review/92675865.](https://reyestr.court.gov.ua/Review/92675865)

### [manual_a56]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.2. Щодо відсутності підстав для визнання протиправним пункту 28 декларації
- **End**: [https://reyestr.court.gov.ua/Review/123081967.](https://reyestr.court.gov.ua/Review/123081967)

### [manual_a57]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.3. Щодо відсутності підстав для визнання протиправним рішення ВККС про
- **End**: [https://reyestr.court.gov.ua/Review/123313999.](https://reyestr.court.gov.ua/Review/123313999)

### [manual_a58]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.4. Щодо неналежності до розгляду суду позову про визнання протиправним
- **End**: [https://reyestr.court.gov.ua/Review/117402606.](https://reyestr.court.gov.ua/Review/117402606)

### [manual_a59]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.5. Щодо обчислення строку повноважень члена ВККС на посаді
- **End**: [https://reyestr.court.gov.ua/Review/102342550.](https://reyestr.court.gov.ua/Review/102342550)

### [manual_a60]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.6. Щодо неналежності до юрисдикції адміністративних судів спорів про
- **End**: [https://reyestr.court.gov.ua/Review/113769374.](https://reyestr.court.gov.ua/Review/113769374)

### [manual_a61]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.7. Щодо відсутності підстав для визнання протиправною бездіяльності ВККС
- **End**: [https://reyestr.court.gov.ua/Review/122769626.](https://reyestr.court.gov.ua/Review/122769626)

### [manual_a62]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.8. Щодо відсутності підстав для визнання протиправними дій Комісії щодо
- **End**: [https://reyestr.court.gov.ua/Review/116512567.](https://reyestr.court.gov.ua/Review/116512567)

### [manual_a63]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.9. Щодо відсутності підстав для визнання протиправними дій Комісії стосовно
- **End**: [https://reyestr.court.gov.ua/Review/124968504](https://reyestr.court.gov.ua/Review/124968504) .

### [manual_a64]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.10. Щодо відсутності підстав для визнання протиправними дій Комісії стосовно
- **End**: [https://reyestr.court.gov.ua/Review/117340688.](https://reyestr.court.gov.ua/Review/117340688)

### [manual_a65]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.11. Щодо відсутності підстав для визнання протиправною бездіяльності ВККС
- **End**: [https://reyestr.court.gov.ua/Review/124904877](https://reyestr.court.gov.ua/Review/124904877) .

### [manual_a66]
- **Category**: (Визначити з контексту)
- **Rule**: Один сегмент = Одна справа = Один JSON
- **Start**: 5.12. Щодо оскарження дій Комісії з оприлюднення набору даних «Інформація про
- **End**: [https://reyestr.court.gov.ua/Review/123314000](https://reyestr.court.gov.ua/Review/123314000) .

