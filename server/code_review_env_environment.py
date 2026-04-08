# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Code Review Env Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

from uuid import uuid4
from typing import List
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import CodeReviewAction, CodeReviewObservation
except ImportError:
    from models import CodeReviewAction, CodeReviewObservation

EASY_CODE = '''void copy(cahr* dst, char* src) {
    strcpy(dst, src);
}
int main(){
    char buf[10];
    copy(buf, "very long string that overflows");
    return 0;
}'''
EASY_BUGS = [
    {"line": 2, "issue": "strcpy no bounds"},
    {"line": 6, "issue": "buffer overflow"},
]

MEDIUM_CODE = '''char* get_input() {
    char* buf = malloc(100);
    gets(buf);
    return buf;
}
int main() {
    char* input = get_input();
    print(input);
    return 0;
}'''
MEDIUM_BUGS = [
    {"line": 2, "issue": "unchecked malloc"},
    {"line": 3, "issue": "unsafe gets"},
    {"line": 4, "issue": "caller must free"},
    {"line": 8, "issue": "format string vulnerability"},
    {"line": 9, "issue": "memory leak"},
]

HARD_CODE = '''int g_counter = 0;
void increment() {
    g_counter++;
}
pthread_mutex_t ma, mb;
void* t1(void* arg) {
    pthread_mutex_lock(&ma);
    pthread_mutex_lock(&mb);
    return NULL;
}
void* t2(void* arg) {
    pthread_mutex_lock(&mb);
    pthread_mutex_lock(&ma);
    return NULL;
}'''
HARD_BUGS = [
    {"line": 1, "issue": "global variable no mutex"},
    {"line": 3, "issue": "race condition"},
    {"line": 8, "issue": "deadlock risk"},
    {"line": 12, "issue": "reverse lock order"},
    {"line": 13, "issue": "deadlock"},
]

TASKS = {
    "easy": {"code": EASY_CODE, "bugs": EASY_BUGS, "file": "easy.c"},
    "medium": {"code": MEDIUM_CODE, "bugs": MEDIUM_BUGS, "file": "medium.c"},
    "hard": {"code": HARD_CODE, "bugs": HARD_BUGS, "file": "hard.c"},
}

def grade(comments, ground_truth: List[dict])-> float:
    if not ground_truth:
        return 0.0
    found = 0
    for bug in ground_truth:
        for c in comments:
            if abs(c.line - bug["line"]) <= 2:
                found += 1
                break
    return round(found /len(ground_truth), 4)

class CodeReviewEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, task_id: str = "easy"):
        self.task_id = task_id
        self.task_id = TASKS.get(task_id, TASKS["easy"])
        self.state = State(episode_id=str(uuid4()), step_count=0)
        self.max_steps = 5

    def reset(self) -> CodeReviewObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        return CodeReviewObservation(
            code=self.task["code"],
            filename=self.task["file"],
            done=False,
            reward=0.0,
        )
    
    def step(self, action: CodeReviewAction) -> CodeReviewObservation:
        self._state.step_count += 1
        score = grade(action.comments, self.task["bugs"])
        done = self._state.step_count >= self.max_steps or score >= 0.8
        return CodeReviewObservation(
            code=self.task["code"],
            filename=self.task["file"],
            done=done,
            reward=score,
            metadata={"step": self._state.step_count, "task": self.task_id}, 
        )
    @property
    def state(self) -> State:
        return self._state



# class CodeReviewEnvironment(Environment):
#     """
#     A simple echo environment that echoes back messages.

#     This environment is designed for testing the HTTP server infrastructure.
#     It maintains minimal state and simply echoes back whatever message it receives.

#     Example:
#         >>> env = CodeReviewEnvironment()
#         >>> obs = env.reset()
#         >>> print(obs.echoed_message)  # "Code Review Env environment ready!"
#         >>>
#         >>> obs = env.step(CodeReviewAction(message="Hello"))
#         >>> print(obs.echoed_message)  # "Hello"
#         >>> print(obs.message_length)  # 5
#     """

#     # Enable concurrent WebSocket sessions.
#     # Set to True if your environment isolates state between instances.
#     # When True, multiple WebSocket clients can connect simultaneously, each
#     # getting their own environment instance (when using factory mode in app.py).
#     SUPPORTS_CONCURRENT_SESSIONS: bool = True

#     def __init__(self):
#         """Initialize the code_review_env environment."""
#         self._state = State(episode_id=str(uuid4()), step_count=0)
#         self._reset_count = 0

#     def reset(self) -> CodeReviewObservation:
#         """
#         Reset the environment.

#         Returns:
#             CodeReviewObservation with a ready message
#         """
#         self._state = State(episode_id=str(uuid4()), step_count=0)
#         self._reset_count += 1

#         return CodeReviewObservation(
#             echoed_message="Code Review Env environment ready!",
#             message_length=0,
#             done=False,
#             reward=0.0,
#         )

#     def step(self, action: CodeReviewAction) -> CodeReviewObservation:  # type: ignore[override]
#         """
#         Execute a step in the environment by echoing the message.

#         Args:
#             action: CodeReviewAction containing the message to echo

#         Returns:
#             CodeReviewObservation with the echoed message and its length
#         """
#         self._state.step_count += 1

#         message = action.message
#         length = len(message)

#         # Simple reward: longer messages get higher rewards
#         reward = length * 0.1

#         return CodeReviewObservation(
#             echoed_message=message,
#             message_length=length,
#             done=False,
#             reward=reward,
#             metadata={"original_message": message, "step": self._state.step_count},
#         )

#     @property
#     def state(self) -> State:
#         """
#         Get the current environment state.

#         Returns:
#             Current State with episode_id and step_count
#         """
#         return self._state
