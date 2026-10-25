# Fusion Squish — szybki start

1. Rozpakuj paczkę lub pobierz repozytorium do stałego folderu.
2. Zainstaluj Python 3.14 i uruchom instalator wewnątrz folderu `FusionSquish`: `Install-mac.command` na macOS lub `Install-Windows.cmd` na Windows.
3. W Fusion naciśnij Shift+S → Add-Ins → dodaj istniejący dodatek. Wskaż folder `FusionSquish` zawierający manifest, nie cały katalog repozytorium.
4. Wybierz FusionSquish → Run i Run on Startup.
5. Uruchom Rozprostuj Mesh → Powierzchnie lub Mesh. Wybierz sąsiednie ściany jednej bryły → OK. Wynikiem jest jeden szkic i jeden DXF z zewnętrznym konturem.
6. Po aktualizacji kodu zamknij całkowicie Fusion i uruchom ponownie.

Płat musi być spójny, otwarty, z jednym obwodem bez otworów. Automatyczne szwy i rozprostowanie płatów z otworami nie są jeszcze obsługiwane.

Pełna instrukcja: `INSTRUKCJA_PL.html` lub `INSTRUKCJA_PL.md`.
Publikacja kodu: `GITHUB_PL.md`.

Silnik jest wykrywany w lokalnym folderze `.engine`. Konfiguracja nie wymaga wpisywania nazwy użytkownika ani ścieżki do jego katalogu domowego. Po przeniesieniu folderu ponownie uruchom instalator, ponieważ samo środowisko Python może zawierać ścieżki instalacyjne.
