from pydantic import BaseModel


class StudyAreaCreate(BaseModel):

    name: str

    description: str | None = None

    boundary: dict


class StudyAreaResponse(BaseModel):

    id: int

    name: str

    description: str | None = None

    boundary: dict