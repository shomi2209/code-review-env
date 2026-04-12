# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Code Review Env Environment.

The code_review_env environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field, model_validator
from typing import List, Union
import json


class ReviewComment(BaseModel):
    """A single review comment on a line of code."""
    line: int = Field(..., description="Line number of the issue")
    severity: str = Field(..., description="HIGH, MEDIUM or LOW")
    issue: str = Field(..., description="Description of the bug")
    fix: str = Field(..., description="How to fix it")


class CodeReviewAction(Action):
    """Action: submit review comments on the code."""
    comments: List[ReviewComment] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_comments(cls, values):
        if isinstance(values, dict):
            comments = values.get("comments")
            if isinstance(comments, str):
                try:
                    values["comments"] = json.loads(comments)
                except Exception:
                    values["comments"] = []
        return values


class CodeReviewObservation(Observation):
    """Observation: code file to review."""
    code: str = Field(default="")
    filename: str = Field(default="")
    done: bool = Field(default=False)
    reward: float = Field(default=0.0)
