# Fusion Squish 1.2.3 — wydanie eksperymentalne

Dodatek do Autodesk Fusion, który rozprostowuje wybrane sąsiednie powierzchnie jednej bryły i tworzy jeden szkic oraz DXF w milimetrach, zawierający tylko zewnętrzny kontur.

## Instalacja

Pobierz i rozpakuj **FusionSquish-1.2.3.zip**. Uruchom instalator silnika w folderze `FusionSquish`, a następnie dodaj ten folder w Fusion przez **Shift+S → Add-Ins**. Wymagany Python 3.12+; testowano 3.14. Pełna instrukcja znajduje się w paczce i pliku `INSTRUKCJA_PL.md`.

Przy aktualizacji kodu zamknij całkowicie Fusion i uruchom ponownie. Ponowna instalacja tych samych bibliotek nie jest potrzebna.

## Zmiany

- Jeden wspólny płat, szkic i DXF zamiast osobnego wyniku dla każdej ściany.
- Poprawione mapowanie ścian do tymczasowej kopii bryły.
- Izolowane uruchomienie silnika, bez przejmowania ustawień Pythona z Fusion.
- Scalanie numerycznych mikroszczelin na brzegach i pomijanie trójkątów o powtórzonych wierzchołkach.
- Alternatywne triangulacje i zachowanie ostatniego wyniku przed przecięciem konturu.
- Raport odkształceń, liczby wykonanych iteracji i lokalna diagnostyka błędów.
- Uniwersalna konfiguracja oraz paczki bez danych konta i prywatnych modeli.

## Status

35 testów automatycznych przeszło na macOS Apple Silicon. Testy API korzystają z atrap; pełny przebieg bieżącej wersji w Fusion wymaga potwierdzenia. Windows nie był testowany.

Wymagany spójny, otwarty płat bez otworów. Brak automatycznych szwów. Krzywizny mogą powodować duże odkształcenia — skontroluj wynik przed cięciem. To wydanie eksperymentalne.

Załączniki nie zawierają lokalnych środowisk Python ani prywatnych modeli i wyników. Informacje o bibliotekach zawiera `THIRD_PARTY.md`.

Kod projektu jest udostępniany na licencji MIT.
