from src.config import RAW_CSV, ensure_directories
from src.delivery_model import run_delivery_model
from src.delivery_diagnostics import run_delivery_diagnostics
from src.demand_forecast import run_demand_forecast
from src.dashboard_exports import create_dashboard_exports
from src.create_dashboard_previews import create_dashboard_previews
from src.load_database import load_database
from src.pricing_analysis import run_pricing_analysis
from src.profile_data import profile_data
from src.run_qa import run_qa


def run_pipeline() -> None:
    ensure_directories()
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"Place DataCoSupplyChainDataset.csv at {RAW_CSV} before running the pipeline."
        )
    profile_data()
    load_database()
    run_qa()
    run_pricing_analysis()
    run_delivery_model()
    run_delivery_diagnostics()
    run_demand_forecast()
    create_dashboard_exports()
    create_dashboard_previews()
    print("Foundation pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()

