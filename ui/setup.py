from core import create_services, get_workflow_service, get_progress_service
from core.viewmodel_builder import ViewModelBuilder

def build_service(db_path: str = "studium.db") -> ViewModelBuilder:
    """
    👷‍♂️ BAU-TEAM DER KÜCHE
    - baut die Service-Kette nach dem KÜCHENPPLAN (core/__init__.py) auf
      und liefert einen einsatzbereiten PROTIONIERER (ViewModelBuilder) für den USER/GAST (UI).
    - verbindet:
        - das LAGER (DB)
        - LAGERVERWALTUNG (Repositories)
        - KÜCHEN-LAGER-KOORDINATION (WorkflowService)
        - KOCH (ProgressService)
        - PORTIONIERER (ViewModelBuilder)

    Technisch
    - verdrahtet Infrastruktur und Services
    - initialisiert Services einmalig und entscheidet, welche Implementierungen verwendet werden
    - kapselt die Service-Erzeugung von der UI
    - die UI erhält ausschließlich einen fertig konfigurierten ViewModelBuilder
      und kennt keine Details über Datenbank oder Repositories.
    - erleichtert Austausch der Infrastruktur (z.B. andere DB)
    """

    # 1) Services global initialisieren (Repositories, Workflow, Progress)
    create_services(db_path)

    # 2) Services holen
    workflow = get_workflow_service()
    progress = get_progress_service()

    # 3) ViewModelBuilder mit den Services aufbauen
    vm_builder = ViewModelBuilder(
        workflow_service=workflow,
        progress_service=progress,
    )

    return vm_builder

    
