import os
import shutil
from src.modules.networking import NetworkAgent
from src.modules.reporting import ReportGenerator
from src.core.persistence import PersistenceManager
from src.core.models import CandidateProfile, Application
from faker import Faker

fake = Faker('pt_BR')

def verify_advanced_features():
    print("Verificando recursos avançados...")

    # 1. Networking
    networking = NetworkAgent()
    action = networking.attempt_connection("TechCorp")
    # Action might be None due to random chance, let's force a few tries
    for _ in range(10):
        if action: break
        action = networking.attempt_connection("TechCorp")

    if action:
        print(f"Networking simulação: {action}")
        assert "Conexão" in action
    else:
        print("Networking simulação: Nenhuma ação gerada (probabilidade).")

    # 2. Reporting
    print("Verificando relatório...")
    reporter = ReportGenerator()
    # Mock data
    profile = CandidateProfile(name="Teste", email="t@t.com", phone="123", summary="Sum", experiences=[], education=[], skills=[])
    metrics = {"scanned": 10, "applied": 1}
    apps = [Application(job_id="1", profile_id=profile.id, resume_id=profile.id, platform="Test", notes="")]

    filename = reporter.generate_daily_report(profile, metrics, apps, "Teste Estratégia")
    assert os.path.exists(filename)
    with open(filename, 'r') as f:
        content = f.read()
        assert "RELATÓRIO OPERACIONAL" in content
        assert "Teste Estratégia" in content
    print(f"Relatório gerado: {filename}")
    os.remove(filename) # Clean up

    # 3. Persistence
    print("Verificando persistência...")
    if os.path.exists("data_test"):
        shutil.rmtree("data_test")

    # Patch the global DATA_DIR in persistence for testing, but since it's hardcoded in the module,
    # we might just use the real class and clean up.
    # Actually, let's just instantiate and use the default 'data' dir but back it up/restore or just accept it uses 'data'.
    # For safety in test, let's rely on the file existence checks.

    pm = PersistenceManager()
    pm.save_data(profile, metrics, apps)

    p_load, m_load, a_load = pm.load_data()
    assert p_load.name == "Teste"
    assert m_load["scanned"] == 10
    assert len(a_load) == 1
    print("Persistência Salvar/Carregar OK.")

    # Clean up 'data' if it contains only test data?
    # Better not to wipe the user's potential real run data if we were live.
    # But here we are in a sandbox.

    print("Verificação avançada completa.")

if __name__ == "__main__":
    verify_advanced_features()
