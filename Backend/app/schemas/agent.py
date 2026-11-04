from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AgentTask = Literal["negotiation", "fraud"]


class AgentRunRequest(BaseModel):
    task: AgentTask
    reference_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
    reference_type: Literal["po", "supplier"] = "supplier"
    instruction: str = Field(default="", max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def negotiation_requires_purchase_order(self) -> "AgentRunRequest":
        if self.task == "negotiation" and self.reference_type != "po":
            raise ValueError("Negotiation requests must reference a purchase order.")
        return self


class AgentChatRequest(BaseModel):
    task: AgentTask
    reference_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$",
    )
    question: str = Field(min_length=1, max_length=1000)

    model_config = ConfigDict(extra="forbid")


class ApprovalDecision(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")


class ApprovalCreate(BaseModel):
    action_type: str = Field(min_length=1, max_length=100)
    reference_type: Literal["po", "supplier"] = "po"
    reference_id: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ApprovalRead(BaseModel):
    id: int
    action_type: str
    reference_type: str
    reference_id: str
    status: str
    payload: dict[str, Any]
    decision_notes: str | None
    created_at: datetime
    decided_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
