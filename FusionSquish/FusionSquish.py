"""Fusion UI adapter; numerical dependencies run outside Fusion's interpreter."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import traceback

import adsk.core
import adsk.fusion

ROOT = Path(__file__).resolve().parent
COMMAND = 'FusionSquish_Flatten'
PANEL = 'SolidScriptsAddinsPanel'
_handlers = []
_busy = False


def ui():
    return adsk.core.Application.get().userInterface


def python_path():
    local = ROOT / '.engine' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if local.is_file():
        return str(local)
    config = ROOT / 'config.json'
    if not config.exists():
        raise RuntimeError('Najpierw uruchom Install-mac.command lub Install-Windows.cmd. Szczegóły w INSTRUKCJA_PL.html.')
    path = Path(json.loads(config.read_text(encoding='utf-8'))['python'])
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise RuntimeError('Nie znaleziono Pythona silnika. Uruchom ponownie instalator.')
    return str(path)


def public_error(error):
    """Avoid displaying local account paths in dialogs and shared screenshots."""
    return str(error).replace(str(ROOT), '<FusionSquish>').replace(str(Path.home()), '~')


def calculate(request):
    interpreter = python_path()
    with tempfile.TemporaryDirectory(prefix='fusion-squish-') as directory:
        folder = Path(directory)
        source, target = folder / 'input.json', folder / 'output.json'
        source.write_text(json.dumps(request), encoding='utf-8')
        progress = ui().createProgressDialog()
        progress.isCancelButtonShown = True
        progress.show('Fusion Squish', 'Obliczanie SLIM… %p%', 0, 100, 0)
        process = None
        try:
            with (folder / 'engine.log').open('w', encoding='utf-8') as log:
                flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                # Fusion sets PYTHONHOME/PYTHONPATH for its embedded runtime.
                # Inheriting these mixes Python installations and breaks libigl
                # with ImportError: std::bad_cast on macOS. Isolate this process.
                process = subprocess.Popen([interpreter, '-I', str(ROOT/'engine'/'solver.py'), str(source), str(target)],
                                           stdout=log, stderr=log, creationflags=flags)
                started = time.monotonic()
                while process.poll() is None:
                    adsk.doEvents()
                    if progress.wasCancelled:
                        raise RuntimeError('Anulowano obliczenia. Nie utworzono szkiców.')
                    if time.monotonic()-started > 600:
                        raise RuntimeError('Przekroczono 10 minut. Zmniejsz siatkę lub liczbę iteracji.')
                    progress.progressValue = min(95, int((time.monotonic()-started)/6))
                    time.sleep(0.05)
            if not target.exists():
                detail = (folder/'engine.log').read_text(encoding='utf-8', errors='replace')[-3000:]
                raise RuntimeError('Silnik zakończył się bez wyniku. Uruchom ponownie instalator.\n'+detail)
            result = json.loads(target.read_text(encoding='utf-8'))
            if not result.get('ok'):
                error = result.get('error', 'Błąd silnika.')
                try:
                    debug_folder = ROOT / '.diagnostics'
                    debug_folder.mkdir(exist_ok=True)
                    (debug_folder/'last_failure.json').write_text(
                        json.dumps({'request': request, 'error': public_error(error)}, ensure_ascii=False), encoding='utf-8')
                    error += '\nZapisano lokalną diagnostykę: <FusionSquish>/.diagnostics/last_failure.json'
                except OSError:
                    pass
                raise RuntimeError(error)
            return result['results']
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            progress.hide()


def collect_meshes(selection, quality):
    """Copy each BRep face into an independent transient surface, then tessellate.

    No persistent BRep/Mesh features are added and source entities are read-only.
    Each selected face is its own pattern; existing MeshBodies remain supported.
    """
    meshes = []
    for i in range(selection.selectionCount):
        entity = selection.selection(i).entity
        face = adsk.fusion.BRepFace.cast(entity)
        if face:
            native = face.nativeObject or face
            name = '{} — powierzchnia {}'.format(face.body.name, i+1)
            temporary = adsk.fusion.TemporaryBRepManager.get().copy(native)
            if not temporary:
                raise RuntimeError('Nie udało się skopiować powierzchni: '+name)
            calculator = temporary.meshManager.createMeshCalculator()
            if not calculator or not calculator.setQuality(quality):
                raise RuntimeError('Nie udało się przygotować triangulacji: '+name)
            mesh = calculator.calculate()
        else:
            body = adsk.fusion.MeshBody.cast(entity)
            if not body:
                raise RuntimeError('Wybierz powierzchnię modelu BRep albo obiekt Mesh.')
            native = body.nativeObject or body
            name = body.name
            mesh = native.displayMesh
        if not mesh or not mesh.triangleCount:
            raise RuntimeError('Nie udało się utworzyć siatki: '+name)
        if mesh.triangleCount > 30000:
            raise RuntimeError(name+': ponad 30 000 trójkątów. Wybierz niższą jakość siatki lub użyj Reduce dla Mesh.')
        indices = mesh.nodeIndices
        meshes.append({'name': name,
                       'vertices': [[p.x,p.y,p.z] for p in mesh.nodeCoordinates],
                       'faces': [indices[j:j+3] for j in range(0,len(indices),3)]})
    return meshes


def collect_combined_mesh(selection, quality):
    """Tessellate a selected BRep patch as one body, with shared edge sampling.

    Copy the owning body and remove unselected faces only on that transient
    copy. Meshing each face separately can create incompatible edge samples.
    """
    entities = [selection.selection(i).entity for i in range(selection.selectionCount)]
    faces = [adsk.fusion.BRepFace.cast(entity) for entity in entities]
    if not entities:
        raise RuntimeError('Zaznacz sąsiednie powierzchnie jednego modelu.')
    if not all(faces):
        if len(entities) == 1 and adsk.fusion.MeshBody.cast(entities[0]):
            return collect_meshes(selection, quality)
        raise RuntimeError('Dla jednego konturu wybierz ściany jednej bryły BRep albo jeden połączony obiekt Mesh. '
                           'Oddzielne obiekty najpierw połącz w Fusion.')
    native_faces = [face.nativeObject or face for face in faces]
    body = native_faces[0].body
    context = faces[0].assemblyContext
    for face, native in zip(faces, native_faces):
        if native.body != body or face.assemblyContext != context:
            raise RuntimeError('Wybierz powierzchnie jednej bryły w tym samym wystąpieniu komponentu. '
                               'Oddzielne bryły najpierw zszyj/połącz w Fusion.')
    manager = adsk.fusion.TemporaryBRepManager.get()
    # Only convert(), not TemporaryBRepManager.copy(), guarantees that
    # original tempIds map to the new body. Keep analytic surfaces unchanged.
    temporary = body.convert(adsk.fusion.BRepConvertOptions.ProceduralToNURBSConversion)
    if not temporary or not temporary.isTemporary:
        raise RuntimeError('Nie udało się utworzyć tymczasowej kopii modelu z mapowaniem powierzchni.')
    retained = []
    seen = set()
    for face in native_faces:
        if face.tempId in seen:
            continue
        seen.add(face.tempId)
        try:
            matches = [adsk.fusion.BRepFace.cast(item) for item in temporary.findByTempId(face.tempId)]
        except RuntimeError as error:
            raise RuntimeError('Fusion nie odnalazł powierzchni w przekonwertowanej kopii modelu: '+str(error)) from error
        matches = [item for item in matches if item]
        if not matches:
            raise RuntimeError('Nie udało się odnaleźć wybranej powierzchni w kopii modelu. Nie utworzono wyniku.')
        # Conversion may split a source face: retain every corresponding face.
        retained.extend(matches)
    if len(retained) < temporary.faces.count and not manager.deleteFaces(retained, False):
        raise RuntimeError('Nie udało się wydzielić wspólnego płata w kopii modelu.')
    calculator = temporary.meshManager.createMeshCalculator()
    if not calculator or not calculator.setQuality(quality):
        raise RuntimeError('Nie udało się przygotować siatki wspólnego płata.')
    mesh = calculator.calculate()
    if not mesh or not mesh.triangleCount:
        raise RuntimeError('Nie udało się utworzyć siatki wspólnego płata.')
    if mesh.triangleCount > 30000:
        raise RuntimeError('Wspólny płat ma ponad 30 000 trójkątów. Wybierz niższą jakość siatki lub mniejszy obszar.')
    def payload(triangulation):
        indices = triangulation.nodeIndices
        return {'vertices': [[p.x,p.y,p.z] for p in triangulation.nodeCoordinates],
                'faces': [indices[j:j+3] for j in range(0,len(indices),3)]}
    result = dict(name=body.name+' — wspólny kontur', **payload(mesh))
    # Independent tessellation settings can avoid a numerical crack in the
    # primary triangulation. The worker tries these only if the primary fails.
    tolerance = calculator.surfaceTolerance
    alternatives = []
    if isinstance(tolerance, (int, float)) and tolerance > 0:
        for factor in (0.5, 2.0):
            try:
                calculator.surfaceTolerance = tolerance*factor
                alternative = calculator.calculate()
                if alternative and 0 < alternative.triangleCount <= 30000:
                    item = payload(alternative)
                    if item != {key: result[key] for key in ('vertices','faces')} and item not in alternatives:
                        alternatives.append(item)
            except RuntimeError:
                continue
        calculator.surfaceTolerance = tolerance
    if alternatives:
        result['alternatives'] = alternatives
    return [result]


def make_sketch(component, result, offset, triangulation):
    sketch = component.sketches.add(component.xYConstructionPlane)
    try:
        sketch.name = 'Squish — '+result['name']
        sketch.isComputeDeferred = True
        uv = result['uv_cm']
        points = [adsk.core.Point3D.create(x+offset, y, 0) for x,y in uv]
        loop = result['boundary']
        lines = sketch.sketchCurves.sketchLines
        boundary_edges = set()
        first, previous = None, None
        for i, a in enumerate(loop):
            b = loop[(i+1) % len(loop)]
            start = points[a] if previous is None else previous
            end = first if i == len(loop)-1 else points[b]
            line = lines.addByTwoPoints(start, end)
            if first is None:
                first = line.startSketchPoint
            previous = line.endSketchPoint
            boundary_edges.add(tuple(sorted((a,b))))
        if triangulation:
            if len(result['edges']) > 10000:
                raise RuntimeError('Podgląd triangulacji ma ponad 10 000 linii. Wyłącz opcję triangulacji.')
            for a,b in result['edges']:
                if tuple(sorted((a,b))) not in boundary_edges:
                    line = lines.addByTwoPoints(points[a], points[b])
                    line.isConstruction = True
        sketch.attributes.add('FusionSquish', 'report', json.dumps(result['stats']))
        return sketch
    except Exception:
        sketch.isComputeDeferred = False
        sketch.deleteMe()
        raise
    finally:
        if sketch.isValid:
            sketch.isComputeDeferred = False


def export_dxf(design, sketch, filename):
    manager = design.exportManager
    if hasattr(manager, 'createDXFSketchExportOptions'):
        options = manager.createDXFSketchExportOptions(filename, sketch)
        options.units = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        options.isConstructionExported = False
        if not manager.execute(options):
            raise RuntimeError('Fusion nie zapisał pliku DXF.')
    else:
        raise RuntimeError('Ta wersja Fusion nie ma nowego API eksportu DXF. Szkic jest gotowy: kliknij go prawym przyciskiem > Save As DXF.')


class Execute(adsk.core.CommandEventHandler):
    def notify(self, args):
        global _busy
        if _busy:
            return
        _busy = True
        created = []
        try:
            inputs = args.command.commandInputs
            design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
            if not design:
                raise RuntimeError('Otwórz projekt w przestrzeni Design / Projektowanie.')
            selection = inputs.itemById('meshes')
            qualities = [adsk.fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh,
                         adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh,
                         adsk.fusion.TriangleMeshQualityOptions.HighQualityTriangleMesh]
            quality = qualities[inputs.itemById('quality').selectedItem.index]
            meshes = collect_combined_mesh(selection, quality)
            results = calculate({'meshes': meshes, 'iterations': inputs.itemById('iterations').value})
            offset = 0.0
            reports = []
            for result in results:
                sketch = make_sketch(design.rootComponent, result, offset, False)
                created.append(sketch)
                offset += max(p[0] for p in result['uv_cm']) + 1.0
                stats = result['stats']
                reports.append('{}\n  maks. zmiana długości krawędzi: {:.2f}%\n  RMS: {:.2f}%; zmiana pola: {:+.2f}%'.format(
                    sketch.name, stats['max_edge_strain_percent'], stats['rms_edge_strain_percent'], stats['area_change_percent']))
                if stats.get('stopped_before_overlap'):
                    reports.append('Zatrzymano po {} iteracjach, przed przecięciem obrysu. '
                                   'Sprawdź odkształcenia przed wykonaniem wykroju.'.format(stats['iterations']))
                if stats.get('removed_collapsed_triangles'):
                    reports.append('Pominięte trójkąty o powtórzonych wierzchołkach: {}'.format(stats['removed_collapsed_triangles']))
                if stats.get('mesh_attempt', 1) > 1:
                    reports.append('Użyto alternatywnej triangulacji nr {}.'.format(stats['mesh_attempt']))
            adsk.core.Application.get().activeViewport.fit()
        except Exception as error:
            for sketch in reversed(created):
                if sketch.isValid:
                    sketch.deleteMe()
            ui().messageBox(public_error(error), 'Fusion Squish — nie utworzono wyniku')
            _busy = False
            return
        try:
            if inputs.itemById('export').value:
                for sketch in created:
                    dialog = ui().createFileDialog()
                    dialog.title = 'Zapisz DXF (mm): '+sketch.name
                    dialog.filter = 'DXF (*.dxf)'
                    dialog.initialFilename = 'Squish.dxf'
                    if dialog.showSave() == adsk.core.DialogResults.DialogOK:
                        filename = dialog.filename
                        if not filename.lower().endswith('.dxf'):
                            filename += '.dxf'
                        export_dxf(design, sketch, filename)
            ui().messageBox('Utworzono szkice na XY głównego komponentu.\n\n'+'\n\n'.join(reports)+
                            '\n\nWynik jest przybliżeniem siatki. Raport nie jest modelem zachowania materiału.\n'
                            'DXF później: prawy przycisk na szkicu > Save As DXF.', 'Fusion Squish — gotowe')
        except Exception as error:
            ui().messageBox('Szkice zostały utworzone, ale eksport DXF nie został ukończony.\n'+public_error(error), 'Fusion Squish')
        finally:
            _busy = False


class Created(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            command = args.command
            inputs = command.commandInputs
            select = inputs.addSelectionInput('meshes', 'Powierzchnie lub Mesh', 'Wybierz sąsiednie powierzchnie jednej bryły — jeden wspólny kontur')
            select.addSelectionFilter('Faces')
            select.addSelectionFilter('MeshBodies')
            select.setSelectionLimits(1, 0)  # Fusion: 0 means no maximum.
            quality = inputs.addDropDownCommandInput('quality', 'Jakość siatki z powierzchni',
                                                      adsk.core.DropDownStyles.TextListDropDownStyle)
            for label, selected in [('Niska — mniej trójkątów', False), ('Normalna', True), ('Wysoka — więcej szczegółów', False)]:
                quality.listItems.add(label, selected)
            inputs.addIntegerSpinnerCommandInput('iterations', 'Iteracje SLIM', 1, 1000, 25, 100)
            inputs.addBoolValueInput('export', 'Zapisz też DXF teraz (mm)', True, '', False)
            inputs.addTextBoxCommandInput('help', '', 'Wszystkie wybrane ściany jednej bryły → jeden płat → jeden szkic i DXF. '
                                          'Tylko zewnętrzny kontur, bez linii podziału. Wybierz spójny otwarty obszar bez otworów.', 3, True)
            handler = Execute()
            command.execute.add(handler)
            _handlers.append(handler)
        except Exception:
            ui().messageBox(public_error(traceback.format_exc()), 'Fusion Squish')


def run(context):
    try:
        interface = ui()
        definition = interface.commandDefinitions.itemById(COMMAND)
        if not definition:
            definition = interface.commandDefinitions.addButtonDefinition(COMMAND, 'Rozprostuj Mesh',
                'Fusion Squish: wybierz powierzchnie modelu lub Mesh i utwórz rozwinięte szkice oraz DXF.', str(ROOT/'resources'/'flatten'))
        handler = Created()
        definition.commandCreated.add(handler)
        _handlers.append(handler)
        workspace = interface.workspaces.itemById('FusionSolidEnvironment')
        panel = workspace.toolbarPanels.itemById(PANEL)
        if not panel:
            raise RuntimeError('Nie znaleziono panelu dodatków w Design.')
        control = panel.controls.itemById(COMMAND) or panel.controls.addCommand(definition)
        control.isPromoted = True
        control.isPromotedByDefault = True
    except Exception:
        ui().messageBox(public_error(traceback.format_exc()), 'Fusion Squish — uruchomienie')


def stop(context):
    workspace = ui().workspaces.itemById('FusionSolidEnvironment')
    panel = workspace.toolbarPanels.itemById(PANEL) if workspace else None
    control = panel.controls.itemById(COMMAND) if panel else None
    if control:
        control.deleteMe()
    definition = ui().commandDefinitions.itemById(COMMAND)
    if definition:
        definition.deleteMe()
    _handlers.clear()
