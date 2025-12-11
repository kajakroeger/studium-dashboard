"""
ui/bootstrap.py
Baut SQLite-Repos + Service zusammen. Kein UI/Business-Code.
"""
from core import create_services, get_workflow_service, get_progress_service
from core.viewmodel_builder import ViewModelBuilder


def build_service(db_path: str = "studium.db") -> ViewModelBuilder:
    """
    Initialisiert die Services (Workflow + Progress) und gibt
    einen ViewModelBuilder zurück, der im Dashboard verwendet wird.
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

    
