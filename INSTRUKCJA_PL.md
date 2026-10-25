# Fusion Squish — wspólny płat → zewnętrzny kontur → DXF

Dodatek do Autodesk Fusion dla macOS i Windows. Wersja 1.2.3.

## Co zmieniło się w wersji 1.2

**Wszystkie wybrane sąsiednie ściany jednej bryły są rozprostowywane razem. Wynik to jeden szkic i jeden DXF z zewnętrznym konturem.** Wewnętrzne krawędzie pomiędzy ścianami i linie triangulacji nie są dodawane do szkicu. Nie ma już opcji triangulacji ani osobnych plików dla każdej ściany.

Wybór nie ma limitu liczby ścian. Wspólny płat musi mieć maksymalnie 30 000 trójkątów oraz 3000 odcinków obwodu. Wybierz spójny obszar jednej bryły, połączony krawędziami, z jednym obwodem, bez otworów. Sąsiadowanie wyłącznie w punkcie nie wystarcza. Ściany z różnych brył lub wystąpień komponentów trzeba wcześniej połączyć/zszyć w Fusion.

Można także wybrać jeden gotowy obiekt Mesh. Wybór pojedynczych trójkątów wewnątrz Mesh oraz łączenie kilku obiektów Mesh tym poleceniem nie są obsługiwane. Dla takiego wejścia przygotuj wcześniej jeden połączony płat siatki.

## Poprawki w wersji 1.2.3

- Trójkąty CAD o powtórzonych wierzchołkach są pomijane jako elementy o zerowej powierzchni. Inne degeneracje nadal powodują błąd; nie wypełniamy otworów.
- Dla wspólnego płata BRep przygotowywane są alternatywne triangulacje z tolerancją 0,5× i 2× ustawienia początkowego. Silnik sięga po nie dopiero po niepowodzeniu pierwszej siatki. Nadal obowiązuje limit 30 000 trójkątów na wariant.
- SLIM zatrzymuje się przed przecięciem obrysu i zwraca ostatni poprawny wynik. Raport zawiera liczbę zaakceptowanych iteracji oraz odkształcenia. Zatrzymanie nie oznacza, że odkształcenia są małe — oceń je przed cięciem.
- Jeśli wszystkie warianty zawiodą, dodatek zapisze lokalnie wejściową geometrię i komunikat do `FusionSquish/.diagnostics/last_failure.json`. Plik jest nadpisywany przy kolejnym błędzie. Nie jest wysyłany do internetu ani dołączany do paczek publikacyjnych.

## Szybki start po aktualizacji

1. Zamknij całkowicie Fusion (na Macu **⌘Q**) i uruchom ponownie. Bibliotek nie trzeba ponownie instalować.
2. Otwórz model w **Design / Projektowanie**.
3. Kliknij **Rozprostuj Mesh**. Nazwa przycisku pozostała taka sama.
4. W polu **Powierzchnie lub Mesh** zaznacz wszystkie sąsiednie ściany, które mają stanowić jeden wykrój. Muszą należeć do jednej bryły i tego samego wystąpienia komponentu.
5. Zostaw **Jakość siatki z powierzchni = Normalna**, **Iteracje SLIM = 100**.
6. Jeśli chcesz od razu zapisać plik, zaznacz **Zapisz też DXF teraz (mm)**.
7. Kliknij **OK**. Dodatek skopiuje bryłę do pamięci, zachowa w kopii wyłącznie wybrane ściany, utworzy jedną siatkę i rozprostuje ją jako całość.
8. Powstanie jeden szkic **Squish — [nazwa bryły] — wspólny kontur** na XY głównego komponentu. Oryginał pozostaje bez zmian; kopia robocza nie pojawia się w drzewie projektu.
9. Zapisz DXF w jednym oknie zapisu. Anulowanie zapisu pozostawia szkic w projekcie.
10. Ukryj model źródłowy i otwórz szkic. Powinien zawierać sam zamknięty obrys, bez podziałów pomiędzy wybranymi ścianami.

Stare szkice i pliki DXF nie są automatycznie scalane ani usuwane. Uruchom polecenie ponownie na modelu źródłowym, aby utworzyć wspólne rozwinięcie. Jeśli nadal widzisz opcję triangulacji lub powstaje wiele szkiców, sprawdź w Scripts and Add-Ins ścieżkę dodatku i zrestartuj Fusion.

## Instalacja na nowym komputerze

1. Rozpakuj **FusionSquish-1.2.3.zip** do stałego folderu. Nie uruchamiaj dodatku z wnętrza ZIP.
2. Zainstaluj 64-bitowy **Python 3.14** z https://www.python.org/downloads/ (minimum 3.12, wymagane dostępne pakiety binarne dla systemu). Na Windows zaznacz dodanie Pythona do PATH.
3. W folderze **FusionSquish**, obok manifestu, uruchom **Install-mac.command** na Macu lub **Install-Windows.cmd** na Windows.
4. Jeśli Mac nie otwiera pliku command: otwórz Terminal, wpisz `cd `, przeciągnij folder FusionSquish do Terminala, naciśnij Enter, wpisz `python3 setup_engine.py` i Enter.
5. Poczekaj na test silnika i komunikat **GOTOWE**. Internet jest potrzebny podczas instalacji bibliotek.
6. W Fusion otwórz **Utilities → Add-Ins → Scripts and Add-Ins**, albo użyj **Shift+S**.
7. W zakładce **Add-Ins** wybierz **+** / istniejący dodatek z urządzenia i wskaż folder **FusionSquish**, zawierający FusionSquish.py oraz FusionSquish.manifest.
8. Zaznacz **FusionSquish → Run** i **Run on Startup**.
9. Przycisk **Rozprostuj Mesh** jest w panelu dodatków w Design / Utilities. Możesz wyszukać go przez **S**.

Po przeniesieniu folderu uruchom ponownie instalator silnika. Silnik jest automatycznie wykrywany w .engine; config.json zawiera ścieżkę względną. Biblioteki są w .engine, oddzielnie od interpretera Fusion. Każdy użytkownik przygotowuje własny silnik instalatorem.

## Przygotowanie trudniejszego modelu

Dla sąsiednich ścian BRep nie musisz ręcznie wykonywać Separate, Keep Body ani Tessellate. Dodatek wydziela wybrany płat z kopii całej bryły i trianguluje go wspólnie, zachowując wspólne krawędzie.

Jeśli wybierzesz całą zamkniętą skorupę, płat z otworami lub kilka rozłącznych obszarów, otrzymasz komunikat zamiast niepoprawnego konturu. Dodatek nie dobiera szwów i nie wypełnia otworów. Pełny bok walca wymaga przecięcia wzdłuż — samo usunięcie den nie wystarcza. Wybierz otwarty fragment lub wcześniej podziel powierzchnie w Fusion.

Dla istniejących siatek:

1. Importuj STL/OBJ/3MF przez **Mesh → Create → Insert Mesh**. Ustaw rzeczywiste jednostki; STL nie zapisuje ich w pliku.
2. Jeśli potrzebujesz fragmentu, użyj **Prepare → Generate Face Groups**, następnie **Modify → Separate → Select Face Groups**. Własną grupę można utworzyć przez **Create Face Group** w Direct Edit.
3. Wydziel jeden połączony obiekt Mesh. Zachowanie kopii oryginału jest opcjonalne; przed zmianami możesz zapisać kopię projektu.
4. Przy **Plane Cut** wybierz **No Fill**, aby cięcie nie zostało zaślepione.
5. Użyj **Reduce**, jeśli siatka przekracza limit, oraz **Repair**, jeśli ma błędy. Nie zamykaj otwartego brzegu wykroju.
6. W dodatku wybierz jeden przygotowany Mesh.

## Ustawienia i edycja szkicu

**Jakość siatki z powierzchni** dotyczy wyłącznie BRep. Normalna jest ustawieniem początkowym; Niska zmniejsza liczbę trójkątów, Wysoka może lepiej odwzorować krzywiznę. Istniejąca siatka Mesh nie jest ponownie triangulowana. Limit 30 000 trójkątów dotyczy całego wspólnego płata.

**Iteracje SLIM:** zacznij od 100. Dla trudniejszych kształtów można spróbować 200–500. Więcej iteracji nie usuwa nieuniknionych odkształceń geometrycznych.

Obliczenia można anulować w oknie postępu; limit oczekiwania wynosi 10 minut. Pasek oznacza czas oczekiwania, a nie rzeczywisty procent wykonanych iteracji.

Szkic jest edytowalną polilinią ze wspólnymi końcami sąsiednich odcinków. Nie ma wewnętrznych krawędzi podziału ani konstrukcyjnej triangulacji. Obrys może zawierać współliniowe odcinki, ponieważ odzwierciedla triangulację. Możesz dodać wymiary, oznaczenia i naddatek przez **Offset**. Wynik jest migawką: zmiany modelu nie aktualizują go automatycznie.

## Eksport DXF później

1. Zakończ edycję szkicu (**Finish Sketch**).
2. W drzewie projektu rozwiń **Sketches**.
3. Kliknij prawym przyciskiem szkic wspólnego konturu i wybierz **Save As DXF** / odpowiednią opcję eksportu szkicu.
4. Wybierz mm, jeśli okno udostępnia jednostki, i zapisz.
5. W programie docelowym otwórz DXF w mm i zmierz znany odcinek. Nie stosuj dopasowania do strony.

Eksport z przycisku dodatku jawnie ustawia mm i pomija konstrukcję. Starsze Fusion bez nowego API eksportu zachowa szkic i poprosi o ręczny zapis. Wcześniej utworzone osobne DXF nie są modyfikowane.

## Próba kontrolna

Importuj **examples/prostokat_100x50_mm.stl** w mm. Uruchom dodatek i wybierz ten jeden obiekt Mesh. Wynik powinien mieć boki około 100 i 50 mm. Kontur może być obrócony na XY. Sprawdź skalę również po otwarciu DXF w programie docelowym.

Drugi przykład, **walec_cwiartka_R100_H50_mm.stl**, daje rozwinięcie o wysokości 50 mm i długości około 157 mm. Siatka opisuje łuk cięciwami, więc długość jest nieco mniejsza niż dokładne πR/2.

Aby sprawdzić wspólne rozwinięcie ścian BRep, wybierz dwie sąsiednie ściany prostej bryły i uruchom dodatek. Oczekiwany wynik: jeden szkic, bez wspólnej krawędzi tych ścian wewnątrz konturu.

## Jak to działa

Dla BRep dodatek kopiuje bryłę poza dokumentem przez BRepBody.convert z opcją ProceduralToNURBSConversion, która zachowuje mapowanie tempId. W kopii odnajduje zaznaczone ściany i usuwa pozostałe przez deleteFaces. Następnie TriangleMeshCalculator trianguluje cały zachowany płat. Wspólna triangulacja pozwala uniknąć niezależnego próbkowania krawędzi każdej ściany. Oryginalna bryła nie jest modyfikowana.

Silnik scala identyczne wierzchołki oraz niemal identyczne punkty na brzegach (tolerancja 0,00001 mm), usuwa trójkąty o powtórzonych wierzchołkach, uzgadnia orientację trójkątów i kontroluje topologię. Parametryzacja harmoniczna daje początkowe odwzorowanie płata na płaszczyznę. SLIM z energią Symmetric Dirichlet optymalizuje je, ograniczając rozciąganie i ściskanie. Każda iteracja jest sprawdzana pod kątem odwróconych trójkątów oraz przecinającego się brzegu. Jeśli kolejna iteracja przecina obrys, zachowywany jest ostatni poprawny wynik i raportowana faktyczna liczba iteracji. Jeśli już pierwsza iteracja jest niepoprawna, operacja zgłasza błąd.

Do szkicu trafiają tylko krawędzie brzegu — te, które należą do jednego trójkąta. Wewnętrzna krawędź między ścianami należy do dwóch trójkątów, dlatego nie jest częścią konturu. To wspólne rozprostowanie geometrii 3D, a nie sklejenie niezależnych rysunków 2D.

Obliczenia odbywają się lokalnie w izolowanym procesie Python. Geometria nie jest wysyłana do internetu. Fusion używa wewnętrznie centymetrów; silnik zachowuje skalę, a eksport zapisuje mm.

Płat sfery lub siodła na ogół wymaga rozciągania, ściskania albo cięć. Raport pokazuje maksymalną bezwzględną zmianę długości krawędzi, jej RMS i zmianę pola. To wskaźniki geometryczne, nie symulacja materiału ani rozwinięcie blachy z grubością i współczynnikiem K. Najpierw wykonaj próbny wykrój.

## Rozwiązywanie problemów

- **Obszar w kształcie L, mimo braku otworów zgłaszany błąd obwodów:** wersja 1.2.3 scala numeryczne mikroszczeliny między brzegami triangulacji. Nie wypełnia rzeczywistych otworów. Komunikat podaje liczbę obwodów i uchwytów. Jeśli problem nadal występuje, potrzebny jest przykładowy model z zaznaczonym obszarem do sprawdzenia triangulacji.

- **3: invalid argument tempId:** wersja 1.2.3 używa BRepBody.convert zamiast zwykłej kopii, aby zachować identyfikatory wybranych ścian. Zamknij całkowicie Fusion i uruchom ponownie. Biblioteki nie wymagają reinstalacji.

- **Kilka plików zamiast jednego:** zrestartuj Fusion i sprawdź, czy uruchamiasz dodatek z aktualnego folderu. Wersja 1.2 tworzy jeden wynik.
- **Powierzchnie nie tworzą jednego płata:** dodaj ściany łączące zaznaczone obszary. Kontakt wyłącznie w punkcie nie wystarcza.
- **Różne bryły lub wystąpienia:** wcześniej zszyj/połącz geometrię w Fusion albo wybierz obszar jednej bryły.
- **Brak mapowania ściany w kopii:** operacja zostaje przerwana, aby nie rozprostować błędnego fragmentu. Zapisz model, ponów zaznaczenie; jeśli problem wraca, przekaż treść komunikatu.
- **Zamknięta siatka / otwory:** potrzebny otwarty płat bez otworów. Przygotuj podział lub szew.
- **Non-manifold / zdegenerowane trójkąty:** napraw model lub siatkę.
- **Za dużo trójkątów:** wybierz Niską jakość BRep lub Reduce dla Mesh. Limit dotyczy całego płata.
- **Kontur przecina sam siebie / duże odkształcenia:** zmień podział powierzchni lub położenie szwów.
- **ImportError: std::bad_cast:** aktualny dodatek uruchamia silnik w izolowanym Pythonie. Zamknij Fusion i uruchom ponownie, aby wczytać poprawkę.
- **Brak silnika / config.json:** uruchom instalator w folderze dodatku. Po przeniesieniu folderu również uruchom go ponownie.
- **Błędny rozmiar:** sprawdź jednostki importu STL i odczytu DXF.
- **Odinstalowanie:** Scripts and Add-Ins → Stop, wyłącz Run on Startup, usuń rejestrację. Szkice pozostaną w zapisanych projektach.

## Weryfikacja i dokumentacja

35 testów automatyczne przeszły na macOS Apple Silicon / Python 3.14. Sprawdzają silnik, izolację uruchamiania, wybór geometrii i nowy wspólny wynik. Test dwóch kwadratów zagiętych o 90° potwierdza jedno rozwinięcie, brak wspólnej krawędzi w obrysie oraz błąd długości poniżej 0,1%. Test adaptera potwierdza utworzenie tylko sześciu odcinków zewnętrznego konturu tego przykładu.

Testy API wykorzystują atrapy interfejsu Fusion. **Kopiowanie bryły, mapowanie ścian i triangulacja przez rzeczywiste jądro Fusion oraz zapis DXF wymagają próby w aplikacji.** Windows nie był testowany. Wyniki geometryczne przykładów nie gwarantują takiej samej dokładności dla dowolnego modelu.

- SLIM / libigl: https://libigl.github.io/libigl-python-bindings/api/igl/
- Tymczasowe BRep: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager.htm
- Wydzielenie ścian: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager_deleteFaces.htm
- Instalacja dodatków: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm

- Mapowanie ścian przy konwersji: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_BRepBody.htm

## Publikacja

Instrukcja przygotowania GitHuba: GITHUB_PL.md. Paczki publikacyjne nie zawierają lokalnych środowisk, konfiguracji ani ścieżek konta użytkownika.
