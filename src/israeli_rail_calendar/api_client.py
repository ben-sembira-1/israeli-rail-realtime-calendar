import asyncio
import logging
from typing import List
import aiohttp
from pydantic import ValidationError

from israeli_rail_calendar.constants import API_URL, HEADERS
from israeli_rail_calendar.models import APIRequestModel, APIResponseModel, TrainRouteModel

async def get_train_schedule(
    session: aiohttp.ClientSession,
    origin_id: str,
    dest_id: str,
    date_str: str,
    semaphore: asyncio.Semaphore
) -> List[TrainRouteModel]:
    payload = APIRequestModel(
        fromStation=origin_id,
        toStation=dest_id,
        date=date_str
    ).model_dump()
    
    async with semaphore:
        async with session.post(API_URL, json=payload, headers=HEADERS) as resp:
            resp.raise_for_status()
            json_data = await resp.json()
            
            try:
                data = APIResponseModel.model_validate(json_data)
            except ValidationError as e:
                logging.error(f"Schema validation error: {e}")
                raise
                
            return data.result.travels
