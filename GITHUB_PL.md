# Przygotowanie repozytorium GitHub

Repozytorium jest niezależne od nazwy użytkownika i miejsca instalacji. Najbezpieczniej publikować zawartość archiwum `dist/FusionSquish-GitHub-source.zip`, które zawiera wyłącznie pliki z listy publikacyjnej. Nie dodawaj do GitHuba całego lokalnego folderu przez przeciągnięcie, ponieważ środowiska Python zawierają pliki instalacyjne i ścieżki komputera.

## Publikacja przez stronę GitHub

1. Utwórz nowe repozytorium o nazwie `FusionSquish`.
2. Rozpakuj `FusionSquish-GitHub-source.zip` do pustego folderu.
3. Wgraj jego zawartość (włącznie z `.gitignore`), zachowując strukturę katalogów. `README.md` powinien być w głównym katalogu repozytorium.
4. Plik ZIP instalacyjny `FusionSquish-<wersja>.zip` możesz dodać jako załącznik do wydania (Release).

Nie publikowano repozytorium automatycznie w ramach przygotowania tych plików.

## Pliki lokalne

`.gitignore` wyklucza `.engine`, `.venv`, `config.json`, ustawienia edytora, cache, logi, pliki systemowe i `dist`. Te pliki są potrzebne tylko lokalnie i mogą zawierać ścieżki użytkownika. Nie są częścią paczek publikacyjnych. `.gitignore` nie usuwa plików już śledzonych w istniejącym repozytorium — sprawdź listę zmian przed zatwierdzeniem.

Konfiguracja generowana przez instalator używa ścieżki względnej. Dodatek automatycznie wykrywa `.engine` dla macOS i Windows. Okna błędów skracają ścieżki katalogu dodatku i katalogu domowego, aby zrzuty nie zawierały ich pełnej postaci.

## Odtworzenie i sprawdzenie paczek

Z głównego katalogu projektu uruchom:

`python3 tools/build_package.py`

Generator tworzy instrukcję HTML, przykłady, ZIP instalacyjny i ZIP źródeł do GitHuba. Korzysta z listy dozwolonych katalogów/typów plików; odrzuca osobiste ścieżki i nazwę konta aktualnego komputera w publikowanych plikach tekstowych. Nie dołącza bibliotek binarnych.

Testy silnika i adaptera: `python -m unittest discover -s tests -v` w środowisku z `FusionSquish/requirements.txt`.

## Licencja

Warunki udostępniania kodu określa plik `LICENSE`. Informacje o zewnętrznych bibliotekach znajdują się w `THIRD_PARTY.md`.

Prywatne modele STEP/F3D, foldery `diagnostics/`, `results/` i `.diagnostics/` również są wykluczone. Dane rzeczywistego modelu i wygenerowane dla niego wykroje nie trafiają do GitHuba ani paczek. Biblioteka OpenCascade użyta do lokalnej analizy nie jest zależnością dodatku.
