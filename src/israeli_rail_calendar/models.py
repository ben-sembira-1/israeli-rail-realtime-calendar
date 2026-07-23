from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RouteConfig(BaseModel):
    origin: str
    destination: str
    filename: str


class TravelMessageModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    message: str


class StopStationModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stationId: int
    arrivalTime: str
    departureTime: str
    platform: Optional[int] = None


class TrainPartModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    departureTime: str
    arrivalTime: str
    trainNumber: int
    orignStation: int
    destinationStation: int
    originPlatform: Optional[int] = None
    destPlatform: Optional[int] = None
    stopStations: List[StopStationModel] = []


class TrainRouteModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    trains: List[TrainPartModel]
    travelMessages: Optional[List[TravelMessageModel]] = []


class ApiResultModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    travels: List[TrainRouteModel] = []


class APIResponseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    result: ApiResultModel


class APIRequestModel(BaseModel):
    fromStation: str
    toStation: str
    date: str
    hour: str = "00:00"
    scheduleType: str = "ByDeparture"
    systemType: str = "2"
    languageId: str = "English"
