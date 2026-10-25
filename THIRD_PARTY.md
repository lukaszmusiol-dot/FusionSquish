# Źródła i zależności

Projekt odniesienia: https://github.com/HermanFjell/Flatten-Surface (HermanFjell).
Opisuje workflow harmonic parameterization + SLIM / Symmetric Dirichlet dla wykrojów.
Nie skopiowano ani nie dołączono kodu tego repozytorium; podczas przeglądu nie znaleziono jawnej licencji repozytorium.

Fusion Squish to nowa integracja publicznego API libigl z Autodesk Fusion. Nie jest oficjalnym dodatkiem Autodesk.

Instalator pobiera pakiety z PyPI; binaria nie są dołączone do ZIP:

- libigl 2.6.3: https://github.com/libigl/libigl-python-bindings — licencje i notices znajdują się w instalowanym pakiecie i repozytorium; libigl zasadniczo MPL-2.0, poszczególne komponenty mogą mieć inne warunki.
- NumPy 2.5.4: https://numpy.org/ — BSD-3-Clause i notices dołączonych bibliotek.
- SciPy 1.18.1: https://scipy.org/ — BSD-3-Clause i notices dołączonych bibliotek.

Silnik używa core SLIM i solverów SciPy, nie modułów copyleft CGAL/Triangle. Przy redystrybucji środowiska z binariami należy zachować pełne licencje instalowanych pakietów i ich zależności. Sama paczka dodatku nie zawiera tych binariów.

Ikony są własną geometrią SVG; generator PNG znajduje się w tools/make_icons.py.
