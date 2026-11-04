import re
from dataclasses import dataclass
from inspect import Parameter, Signature
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel


class NotImplementedResponse(BaseModel):
    detail: str


@dataclass(frozen=True)
class EndpointContract:
    method: str
    path: str
    operation_id: str
    summary: str
    has_body: bool = False


def add_placeholder(router: APIRouter, contract: EndpointContract) -> None:
    path_parameters = re.findall(r"{([^}]+)}", contract.path)

    async def not_implemented(request: Request, **kwargs: Any) -> None:
        raise HTTPException(
            status_code=501,
            detail=f"{contract.method} {contract.path} is not implemented yet.",
        )

    parameters = [
        Parameter(
            "request",
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Request,
        ),
        *(
            Parameter(
                name,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=str,
            )
            for name in path_parameters
        ),
    ]
    if contract.has_body:
        parameters.append(
            Parameter(
                "payload",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Body(...),
                annotation=dict[str, Any],
            )
        )
    not_implemented.__signature__ = Signature(
        parameters,
        return_annotation=None,
    )

    router.add_api_route(
        contract.path,
        not_implemented,
        methods=[contract.method],
        name=contract.operation_id,
        operation_id=contract.operation_id,
        summary=contract.summary,
        status_code=501,
        response_model=NotImplementedResponse,
    )


def register_contracts(
    router: APIRouter,
    contracts: tuple[EndpointContract, ...],
) -> APIRouter:
    for contract in contracts:
        add_placeholder(router, contract)
    return router

