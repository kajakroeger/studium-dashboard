from models.bearbeitung import StatusBearbeitung


def debug_bearbeitungszeit_detailliert(service, student_id: int):
    """Zeigt jeden Schritt der Berechnung."""
    
    print("=" * 80)
    print("DEBUG: Bearbeitungszeit - Detaillierte Analyse")
    print("=" * 80)
    
    # ==================== Schritt 1: Bearbeitungen laden ====================
    print("\n[1] BEARBEITUNGEN LADEN")
    print("-" * 40)
    
    bearbeitungen = service.bearbeitungen_fuer_student(student_id)
    print(f"✅ Gesamt: {len(bearbeitungen)} Bearbeitungen")
    
    # ==================== Schritt 2: Status prüfen ====================
    print("\n[2] STATUS-FILTER (nur ABGESCHLOSSEN)")
    print("-" * 40)
    
    for i, b in enumerate(bearbeitungen, start=1):
        status = b.status
        status_str = status.value if hasattr(status, 'value') else str(status)
        print(f"  Bearbeitung {i}: Status = {status_str} (Type: {type(status).__name__})")
        
        if status == StatusBearbeitung.ABGESCHLOSSEN:
            print(f"    ✅ Status ist ABGESCHLOSSEN")
        else:
            print(f"    ❌ Status ist NICHT abgeschlossen → wird übersprungen")
    
    abgeschlossene = [
        b for b in bearbeitungen
        if b.status == StatusBearbeitung.ABGESCHLOSSEN
    ]
    print(f"\n✅ Nach Status-Filter: {len(abgeschlossene)} abgeschlossene Bearbeitungen")
    
    # ==================== Schritt 3: Daten prüfen ====================
    print("\n[3] DATEN-VOLLSTÄNDIGKEIT (start_datum + abgabe_datum)")
    print("-" * 40)
    
    for i, b in enumerate(abgeschlossene, start=1):
        print(f"\n  Bearbeitung {i}:")
        print(f"    start_datum: {b.start_datum} (Type: {type(b.start_datum).__name__})")
        print(f"    abgabe_datum: {b.abgabe_datum} (Type: {type(b.abgabe_datum).__name__})")
        
        if b.start_datum and b.abgabe_datum:
            tage = (b.abgabe_datum - b.start_datum).days
            print(f"    ✅ Beide Daten vorhanden → Bearbeitungszeit: {tage} Tage")
        else:
            if not b.start_datum:
                print(f"    ❌ start_datum fehlt!")
            if not b.abgabe_datum:
                print(f"    ❌ abgabe_datum fehlt!")
    
    mit_daten = [
        b for b in abgeschlossene
        if b.start_datum and b.abgabe_datum
    ]
    print(f"\n✅ Nach Daten-Filter: {len(mit_daten)} Bearbeitungen mit vollständigen Daten")
    
    # ==================== Schritt 4: Kurse & ECTS prüfen ====================
    print("\n[4] KURSE & ECTS-WERTE")
    print("-" * 40)
    
    valide = []
    
    for i, b in enumerate(mit_daten, start=1):
        print(f"\n  Bearbeitung {i}:")
        
        # Kurs laden
        kurs = service.kurs_by_id(b.kurs_id)
        if not kurs:
            print(f"    ❌ Kurs mit ID {b.kurs_id} nicht gefunden!")
            continue
        
        print(f"    Kurs: {kurs.name} (ID: {kurs.id})")
        print(f"    ECTS: {kurs.ects}")
        
        if not kurs.ects or kurs.ects <= 0:
            print(f"    ❌ Kurs hat keine ECTS-Werte (ects={kurs.ects})")
            continue
        
        # Bearbeitungszeit berechnen
        tage = (b.abgabe_datum - b.start_datum).days
        print(f"    Bearbeitungszeit: {tage} Tage")
        
        # Normierung auf 5 ECTS
        normiert = tage * (5.0 / float(kurs.ects))
        print(f"    Normiert auf 5 ECTS: {normiert:.1f} Tage")
        print(f"    ✅ Valide für Berechnung")
        
        valide.append((b, kurs, tage, normiert))
    
    print(f"\n✅ Nach ECTS-Filter: {len(valide)} valide Bearbeitungen")
    
    # ==================== Schritt 5: Durchschnitt berechnen ====================
    print("\n[5] DURCHSCHNITTS-BERECHNUNG")
    print("-" * 40)
    
    if not valide:
        print("❌ KEINE validen Bearbeitungen für Berechnung!")
        print("\nMÖGLICHE URSACHEN:")
        print("  1. Bearbeitungen haben falschen Status")
        print("  2. start_datum oder abgabe_datum fehlt")
        print("  3. Kurse haben keine ECTS-Werte")
        print("\nLÖSUNG:")
        print("  → Prüfe deine Testdaten in der Datenbank")
        print("  → Stelle sicher, dass Kurse ECTS-Werte haben")
        return None
    
    # Durchschnitt berechnen
    total = sum(normiert for _, _, _, normiert in valide)
    count = len(valide)
    durchschnitt = round(total / count, 1)
    
    print(f"  Summe normierter Zeiten: {total:.1f} Tage")
    print(f"  Anzahl Bearbeitungen: {count}")
    print(f"  ✅ DURCHSCHNITT: {durchschnitt:.1f} Tage pro 5 ECTS")
    
    # ==================== Schritt 6: Was Service-Methode zurückgibt ====================
    print("\n[6] SERVICE-METHODEN-TEST")
    print("-" * 40)
    
    result = service.bearbeitungszeit(student_id)
    print(f"  service.bearbeitungszeit({student_id}) = {result}")
    
    if result is None:
        print("  ❌ Service gibt None zurück!")
        print("\n  MÖGLICHE URSACHEN:")
        print("    1. Service-Methode hat andere Filter als oben")
        print("    2. Fehler in der Service-Implementierung")
        print("\n  AKTION: Prüfe core/progress_service.py → bearbeitungszeit()")
    elif result != durchschnitt:
        print(f"  ⚠️  Service-Ergebnis ({result}) ≠ Erwarteter Wert ({durchschnitt})")
        print("  AKTION: Service-Methode nutzt andere Logik")
    else:
        print(f"  ✅ Service-Ergebnis stimmt überein!")
    
    # ==================== Schritt 7: Notenschnitt prüfen ====================
    print("\n[7] NOTENSCHNITT-TEST")
    print("-" * 40)
    
    notenschnitt = service.berechne_notenschnitt(student_id)
    print(f"  service.berechne_notenschnitt({student_id}) = {notenschnitt}")
    
    if notenschnitt is None:
        print("  ❌ Notenschnitt ist None!")
        
        # Prüfen ob Prüfungen vorhanden
        noten = service.alle_bestandenen_noten(student_id)
        print(f"  Bestandene Noten: {noten}")
        
        if not noten:
            print("  PROBLEM: Keine bestandenen Prüfungen gefunden")
            print("  LÖSUNG: Prüfungen mit Noten und bestanden=True anlegen")
    else:
        print(f"  ✅ Notenschnitt: {notenschnitt:.2f}")
    
    print("\n" + "=" * 80)
    print("DEBUG ENDE")
    print("=" * 80)
    
    return result