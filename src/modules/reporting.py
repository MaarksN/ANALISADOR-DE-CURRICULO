import os
from datetime import datetime
from src.core.models import CandidateProfile, Application

class ReportGenerator:
    def __init__(self):
        pass

    def generate_daily_report(self, profile: CandidateProfile, metrics: dict, applications: list[Application], strategy: str):
        """Generates a markdown report of the system's operation."""
        filename = f"relatorio_operacional_{datetime.now().strftime('%Y%m%d')}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# RELATÓRIO OPERACIONAL HUB DE VAGAS - {datetime.now().strftime('%d/%m/%Y')}\n\n")

            f.write("## 1. RESUMO EXECUTIVO\n")
            f.write(f"- **Perfil Ativo:** {profile.name}\n")
            f.write(f"- **Estratégia Atual:** {strategy}\n")
            f.write(f"- **Status:** Operacional\n\n")

            f.write("## 2. MÉTRICAS DO CICLO\n")
            f.write("| Métrica | Valor |\n")
            f.write("|---|---|\n")
            f.write(f"| Vagas Escaneadas | {metrics.get('scanned', 0)} |\n")
            f.write(f"| Vagas Compatíveis | {metrics.get('matched', 0)} |\n")
            f.write(f"| Candidaturas Enviadas | {metrics.get('applied', 0)} |\n")
            f.write(f"| Entrevistas Agendadas | {metrics.get('interviews', 0)} |\n")
            f.write(f"| Ações de Networking | {metrics.get('networking', 0)} |\n\n")

            f.write("## 3. REGISTRO DE CANDIDATURAS (Últimas 10)\n")
            if not applications:
                f.write("_Nenhuma candidatura registrada._\n")
            else:
                for app in applications[-10:]:
                    f.write(f"- **{app.applied_at.strftime('%H:%M')}**: {app.job_id} via {app.platform} - Status: {app.status}\n")

            f.write("\n## 4. PRÓXIMOS PASSOS AUTOMÁTICOS\n")
            f.write("- Manter varredura de vagas.\n")
            f.write("- Acompanhar retornos de networking.\n")
            f.write("- Otimizar currículo baseado em feedback (simulado).\n")

        return filename
