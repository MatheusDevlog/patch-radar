from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RepoCategory = Literal[
    "emulador", "port", "linux", "windows", "mac", "driver", "ferramenta"
]
ImpactLevel = Literal["baixo", "medio", "alto"]


class Repository(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: int | None = None
    owner: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: RepoCategory
    created_at: datetime | None = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class ReleaseRaw(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    repo_name: str = Field(min_length=1)
    tag_name: str = Field(min_length=1)
    published_at: datetime
    body: str = ""
    url: str = Field(min_length=1)


class ChangelogChunk(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    chunk_id: str = Field(min_length=1)
    repo_name: str = Field(min_length=1)
    tag_name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    url: str = Field(min_length=1)


class ReleaseSummary(BaseModel):
    repo_name: str
    version: str
    impact_level: ImpactLevel
    categories: list[str] = Field(default_factory=list)
    summary_pt: str
    highlights: list[str] = Field(default_factory=list)


class ChangelogAnswer(BaseModel):
    question: str
    answer_pt: str
    cited_versions: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
