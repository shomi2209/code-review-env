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
from pydantic import Field
from typing import List

class ReviewComment(Action):
    line: int = Field(..., description="Line number of the issue")
    severity: str = Field(..., description="HIGH,MEDIUM or LOW")
    issue: str = Field(..., description="Description of the bug")
    fix: str = Field(..., description="How to fix it")


class CodeReviewAction(Action):
    comments: List[ReviewComment] = Field(default_factory=list)


class CodeReviewObservation(Observation):
    code: str = Field(default="")
    filename: str = Field(default="")
    done: bool = Field(default=False)
    reward: float = Field(default=0.0)


# class CodeReviewAction(Action):

#     """Action for the Code Review Env environment - just a message to echo."""

#     message: str = Field(..., description="Message to echo back")


# class CodeReviewObservation(Observation):
#     """Observation from the Code Review Env environment - the echoed message."""

#     echoed_message: str = Field(default="", description="The echoed message")
#     message_length: int = Field(default=0, description="Length of the echoed message")
