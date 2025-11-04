"""
App-Einstiegspunkt für das Studium Dashboard.

Start:
    streamlit run app.py
"""

from ui.streamlit_dashboard_ui import StreamlitDashboardUI, _build_service


def main() -> None:
    # Datenbankpfad kannst du hier anpassen oder aus env lesen
    db_path = "studium.db"

    # Service + Repositories aufbauen
    service, student_repo = _build_service(db_path)

    # Dashboard-UI starten
    ui = StreamlitDashboardUI(service, student_repo)
    ui.zeige_dashboard()


if __name__ == "__main__":
    main()
