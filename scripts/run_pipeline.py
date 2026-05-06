import subprocess
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Paths dos scripts existentes
ETL_BACKLOG_SCRIPT = ROOT_DIR.parent / "ETL_Backlog_SGP" / "etl_backlog_sgp.py"
ETL_PRODUCAO_SCRIPT = ROOT_DIR.parent / "ETL_Producao_SGP" / "etl_producao_sgp.py"
BUILD_D_PROJETOS_SCRIPT = ROOT_DIR / "scripts" / "build_d_projetos.py"
AUDITORIA_SCRIPT = ROOT_DIR.parent / "auditoria_integridade_projetos.py"

# Paths de output/artefatos
ONE_DRIVE_BASE = Path(r"C:\Users\Z181040\OneDrive - Claro SA")
RAW_BACKLOG_DIR = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "Base_Dados_SGP" / "Bases_Originais"
RAW_PRODUCAO_DIR = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "Base_Dados_SGP" / "Bases_Originais"
RAW_CONTROLE_PATH = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "GCC GOVERNO - Acompanhamento de Projetos" / "Base de dados e controle" / "Controle_Projetos.xlsx"
RAW_DIARIO_PATH = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "Diario_Bordo" / "BD_Diario_Bordo" / "f_Diario_Bordo.xlsx"

PROCESSED_BACKLOG_PATH = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "Base_Dados_SGP" / "Bases_Processadas_Python" / "BD_Backlog_SGP.xlsx"
PROCESSED_PRODUCAO_PATH = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "Base_Dados_SGP" / "Bases_Processadas_Python" / "BD_Produção_Analitica.xlsx"
PROJETO_DIM_PATH = ONE_DRIVE_BASE / "BASES" / "Projetos_GOV" / "Diario_Bordo" / "BD_DIM" / "d_Projetos.xlsx"


def run_command(command: list[str], cwd: Path | None = None) -> None:
    print(f"Executando: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd or ROOT_DIR, shell=False)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falhou: {' '.join(command)}")


def execute_etl_backlog() -> None:
    if not ETL_BACKLOG_SCRIPT.exists():
        raise FileNotFoundError(f"Script ETL Backlog não encontrado: {ETL_BACKLOG_SCRIPT}")
    run_command([sys.executable, str(ETL_BACKLOG_SCRIPT)])


def execute_etl_producao() -> None:
    if not ETL_PRODUCAO_SCRIPT.exists():
        raise FileNotFoundError(f"Script ETL Produção não encontrado: {ETL_PRODUCAO_SCRIPT}")
    run_command([sys.executable, str(ETL_PRODUCAO_SCRIPT)])


def execute_build_d_projetos() -> None:
    if not BUILD_D_PROJETOS_SCRIPT.exists():
        raise FileNotFoundError(f"Script build_d_projetos não encontrado: {BUILD_D_PROJETOS_SCRIPT}")
    run_command([sys.executable, str(BUILD_D_PROJETOS_SCRIPT)])


def execute_auditoria_integridade() -> None:
    if not AUDITORIA_SCRIPT.exists():
        raise FileNotFoundError(f"Script de auditoria não encontrado: {AUDITORIA_SCRIPT}")
    run_command([sys.executable, str(AUDITORIA_SCRIPT)])


def main() -> None:
    print("=== Pipeline SGP — execução de integração ===")

    print("1. ETL Backlog")
    execute_etl_backlog()

    print("2. ETL Produção")
    execute_etl_producao()

    print("3. Build d_Projetos")
    execute_build_d_projetos()

    print("4. Auditoria de integridade")
    execute_auditoria_integridade()

    print("=== Pipeline concluído ===")


if __name__ == "__main__":
    main()
