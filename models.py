 # Pydantic data models
from pydantic import BaseModel
from typing import List, Optional, Dict

class Room(BaseModel):
    name: str
    area_sqft: float
    zone: str  # "public", "private", "service"
    adjacencies: List[str] = []
    natural_light: bool = False

class StructuredBrief(BaseModel):
    total_area_sqft: float
    plot_width_ft: Optional[float] = None
    plot_depth_ft: Optional[float] = None
    rooms: List[Room]
    special_constraints: List[str] = []

class RoomLayout(BaseModel):
    name: str
    x: float   # feet from origin
    y: float
    width: float
    height: float
    zone: str
    natural_light: bool = False