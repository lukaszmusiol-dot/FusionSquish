# Fusion Squish

**Wybrane powierzchnie Autodesk Fusion → wspólne rozwinięcie → szkic → DXF z zewnętrznym konturem.**

Fusion Squish to eksperymentalny dodatek dla macOS i Windows. Wybiera sąsiednie ściany jednej bryły BRep, tworzy ich tymczasową kopię, trianguluje cały płat i rozprostowuje go metodą SLIM. Wynikiem jest jeden edytowalny szkic na XY i opcjonalnie jeden plik DXF w milimetrach. Model źródłowy pozostaje bez zmian.

![Ikona Fusion Squish](FusionSquish/resources/flatten/64x64.png)

## Pobieranie i instalacja

Aktualna wersja: **1.2.3**. Paczka instalacyjna: **FusionSquish-1.2.3.zip** w załącznikach wydania GitHub lub folderze `packages` repozytorium. Paczkę można też zbudować ze źródeł.

1. Rozpakuj paczkę do stałego folderu.
2. Zainstaluj 64-bitowy Python 3.14.
3. W folderze `FusionSquish` uruchom `Install-mac.command` (macOS) lub `Install-Windows.cmd` (Windows).
4. W Fusion otwórz **Shift+S → Add-Ins**, dodaj istniejący dodatek i wskaż folder `FusionSquish` zawierający manifest.
5. Kliknij **Run** i zaznacz **Run on Startup**.
6. Uruchom **Rozprostuj Mesh**, wybierz sąsiednie powierzchnie jednej bryły i kliknij **OK**. Opcja **Zapisz też DXF teraz (mm)** zapisuje kontur.

Pełna [instrukcja po polsku](INSTRUKCJA_PL.md) opisuje ustawienia, przygotowanie modelu, eksport i rozwiązywanie problemów. [Szybki start](START_TUTAJ.md) zawiera skróconą instrukcję. W paczce jest również instrukcja HTML do otwarcia lokalnie.

## Możliwości

- Wspólne rozprostowanie zaznaczonych ścian jednej bryły, bez limitu liczby zaznaczeń.
- Obsługa jednego gotowego, otwartego obiektu Mesh.
- Jeden szkic i jeden DXF z obrysem, bez wewnętrznych krawędzi podziału.
- Raport zmian długości krawędzi i pola.
- Łączenie numerycznych mikroszczelin, pomijanie trójkątów o powtórzonych wierzchołkach i alternatywne triangulacje.
- Zatrzymanie na ostatniej poprawnej iteracji przed przecięciem obrysu.
- Obliczenia lokalne, w osobnym procesie Python; geometria nie jest wysyłana do internetu.

## Ograniczenia i status

**Wersja eksperymentalna. Nie zakładaj, że wynik nadaje się bez kontroli do cięcia lub produkcji.** Powierzchnie o podwójnej krzywiźnie mogą wymagać dużego rozciągania lub ściskania. Sprawdź raport odkształceń, skalę DXF i wykonaj próbny wykrój.

Płat musi być połączony krawędziami, otwarty i mieć jeden obwód bez otworów. Dodatek nie dobiera automatycznie szwów, nie wypełnia otworów i nie łączy różnych brył. Limit siatki: 30 000 trójkątów i 3000 odcinków obwodu. Nie jest to blachowy Flat Pattern ani fizyczna symulacja materiału.

35 testów automatycznych silnika i adaptera przeszło na macOS Apple Silicon / Python 3.14.2. Testy adaptera wykorzystują atrapy API. Dodatkowo sprawdzono silnik na rzeczywistym STEP triangulowanym niezależnym narzędziem. Pełny przebieg bieżącej wersji w Fusion wymaga potwierdzenia. Windows nie był testowany.

## Wymagania

- Autodesk Fusion na macOS lub Windows.
- Python 3.12+ z dostępnymi pakietami binarnymi; testowano Python 3.14.
- NumPy, SciPy i libigl w wersjach z `FusionSquish/requirements.txt` — instalator pobiera je automatycznie.
- Internet podczas instalacji zależności. Późniejsze obliczenia działają lokalnie.

## Rozwój i budowanie paczek

- `FusionSquish/FusionSquish.py` — interfejs Fusion, geometria, szkice i eksport.
- `FusionSquish/engine/solver.py` — kontrola topologii i rozprostowanie SLIM.
- `tests/` — testy silnika i adaptera.
- `examples/` — dwa przykładowe pliki STL w mm.

W środowisku z zależnościami uruchom:

```sh
python -m unittest discover -s tests -v
python tools/build_package.py
```

Generator zapisuje ZIP instalacyjny i oczyszczoną paczkę źródłową w `dist/`. Więcej informacji: [przygotowanie publikacji](GITHUB_PL.md) oraz [opis wydania](RELEASE_NOTES.md).

## Prywatność i źródła

Lokalne środowiska, konfiguracja, logi, modele użytkownika i wyniki nie są publikowane. Jeśli obliczenia zawiodą, lokalny plik `FusionSquish/.diagnostics/last_failure.json` może zawierać geometrię modelu; nie jest wysyłany ani dołączany do paczek.

Inspiracja: [HermanFjell/Flatten-Surface](https://github.com/HermanFjell/Flatten-Surface). Integracja jest niezależną implementacją korzystającą z libigl; kod repozytorium odniesienia nie jest dołączony. Szczegóły zależności: [THIRD_PARTY.md](THIRD_PARTY.md).

Projekt nie ma jeszcze określonej licencji własnego kodu. Nie należy zakładać, że samo publiczne udostępnienie oznacza licencję open source.
