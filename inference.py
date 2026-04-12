#!/usr/bin/env python3
import os
import json
import asyncio
import requests
from typing import List
from openai import OpenAI

# ── Mandatory env vars ────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY      = os.getenv("OPENAI_API_KEY")
HF_TOKEN     = os.getenv("HF_TOKEN")
ENV_URL      = os.getenv("ENV_URL", "https://shomi2209-code-review-env.hf.space")

TASK_NAME               = "easy"
BENCHMARK               = "code_review_env"
MAX_STEPS               = 5
MAX_TOTAL_REWARD        = 1.0
SUCCESS_SCORE_THRESHOLD = 0.7

# ── Log helpers ───────────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error=None):
    print(f"[STEP] step={step} reward={reward:.4f} done={done}", flush=True)
    if error:
        print(f"[STEP] error={error}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    total_reward = sum(rewards)
    print(f"[END] success={success} steps={steps} score={score:.4f} total_reward={total_reward:.4f}", flush=True)

# ── Environment HTTP calls ────────────────────────────────────────────────────
def env_reset(task_id: str = "easy") -> dict:
    try:
        resp = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[DEBUG] reset failed: {e}", flush=True)
        return {"code": "", "filename": "", "done": True, "reward": 0.0}

def env_step(comments: list) -> dict:
    try:
        payload = {"action": {"comments": comments}}
        resp = requests.post(f"{ENV_URL}/step", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[DEBUG] step failed: {e}", flush=True)
        return {"observation": {"done": True}, "reward": 0.0, "done": True}

# ── LLM call ─────────────────────────────────────────────────────────────────
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
                {"role": "user", "content": f"Review this code:\n\n{code}"},
            ],
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        # strip markdown code fences if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return result.get("comments", [])
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return []

# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset environment
        observation = env_reset(TASK_NAME)
        code = observation.get("code", "")
        done = observation.get("done", False)

        for step in range(1, MAX_STEPS + 1):
            if done or not code:
                break

            # Get LLM response
            comments = get_model_response(client, code)

            # Step environment
            result = env_step(comments)
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            obs = result.get("observation", {})
            code = obs.get("code", code)

            rewards.append(float(reward))
            steps_taken = step

            log_step(
                step=step,
                action=str(comments),
                reward=float(reward),
                done=done,
            )

            if done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Unexpected error: {e}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
