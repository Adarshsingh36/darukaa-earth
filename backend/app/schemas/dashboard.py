from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_projects: int
    total_sites: int
    total_area_hectares: float
    total_carbon_tonnes: float
    average_biodiversity_index: float
