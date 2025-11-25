from typing import List
from datetime import datetime
from pydantic import BaseModel, Field

class ExtractionResult(BaseModel):
    """
    Structure of information extracted from raw text by the LLM.
    This is the input for the saving process.
    """
    essence: str = Field(
        ...,
        description="Factual, concise summary of the event."
    )
    dominant_emotions: List[str] = Field(
        ...,
        description="The 3 most characteristic emotions of the situation as tags (e.g., ['Disappointment', 'Curiosity', 'Determination'])."
    )
    memory_weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Importance of the memory between 0.0 (noise) and 1.0 (life-changing)."
    )
    the_lesson: str = Field(
        ...,
        description="Action-oriented lesson for the future. (What should be done differently?)"
    )


class RankedMemory(BaseModel):
    """
    Final result of the search and ranking process.
    This structure is passed to the Prompt Builder and the Worker.
    """
    id: str
    essence: str
    lesson: str
    emotions: List[str]
    score: float            # Calculated relevance score (0.0 - 1.0+)
    room_id: str            # Source room of the memory
    created_at: datetime    # Creation timestamp
    usage_count: int        # How many times it has been used (statistics)