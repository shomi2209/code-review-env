#!/usr/bin/env python3
import os
import sys
import asyncio
import json
from typing import List
from openai import OpenAI

API_BASE_URL                   = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME                     = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY                        = os.getenv("OPEN_API_KEY")

TASK_NAME                      = "easy"
BENCHMARK                      = "code_review_env"
MAX_STEPS                      = 5
MAX_TOTAL_REWARD               = 1.0
SUCCESS_SCORE_THRESHOLD        = 0.7

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}, flush=True")

def log_step(step: int, action: str, reward: float, done: bool, error=None):
    print(f"[STEP] step={step} reward={reward: .4f} done={done}. flush=True")
    if error:
        print(f"[STEP] error={error}", flush=True)

def  log_end(success: bool, steps: int, score: float, rewards: List[float]):
    total_reward = sum(rewards)
    print(f"[END] success steps={steps} score={score:.4f} total_reward={total_reward:.4f}", flush=True)

def get_model_response(client: OpenAI, code: str) -> list:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a code reviewer. Return JSON only.\n"
                        "Format: {\"comments\": [{\"line\": 2, \"severity\": \"HIGH\","
                        " \"issue\": \"describe bug\", \"fix\": \"how to fix\"}]}"
                    ),
                },
                {"role": "user", "content": f"Review this code: \n\n{code}"},
            ],
            temperature=0.0,                
        )
        result = json.loads(response.choices[0].message.content)
        return  result.get("comments", [])
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return []

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    sys.path.append("server")
    from code_review_env_environment import CodeReviewEnvironment
    from models import CodeReviewAction, ReviewComment

    env = CodeReviewEnvironment(task_id=TASK_NAME)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        observation = env.reset()

        for step in range(1, MAX_STEPS+1):
            if observation.done:
                break

            comments_data = get_model_response(client, observation.code)
            comments = [ReviewComment(**c) for c in comments_data]
            action = CodeReviewAction(comments=comments)

            observation = env.step(action)
            rewards.append(observation.reward)
            steps_taken = step

            log_step(
                step=step,
                action=str(action.model_dump()),
                reward=observation.reward,
                done=observation.done,
            )

            if observation.done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
        
