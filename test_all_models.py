#!/usr/bin/env python3
"""Test all models against one real polydefinite item."""
import os, json, time, sys, ssl
from openai import OpenAI, AzureOpenAI
from urllib.request import Request, urlopen

KEY = os.environ.get("AZURE_KEY", "")
if not KEY:
    print("ERROR: export AZURE_KEY='your-key' first")
    sys.exit(1)

ENDPOINT_AI = "https://crete-xamoulis-resource.services.ai.azure.com/openai/v1"
ENDPOINT_OAI = "https://crete-xamoulis-resource.cognitiveservices.azure.com/"

SYSTEM = (
    "Κάθε παράδειγμα αποτελείται από ένα κείμενο στα Νέα Ελληνικά. "
    "Καλείσαι να δηλώσεις εάν η τελευταία πρόταση του κάθε κειμένου "
    "είναι σημασιολογικά κατάλληλη με βάση το κείμενο που προηγείται αυτής. "
    "Απάντησε ΜΟΝΟ με έναν αριθμό από 1 έως 10."
)

CONTEXT = "Ο Γιώργος είχε έξι γάτες, όλες μαύρες. Όταν έφευγε ταξίδι, τις άφηνε να τις φροντίζει ο γείτονας."
SENTENCE = "Οι μαύρες γάτες αγαπούσαν τον γείτονα."
USER_MSG = f"{CONTEXT} {SENTENCE}"

MODELS = [
    ("gpt-4o",                   "azure_openai", "gpt-4o",                   False),
    ("gpt-5.4-pro",              "gpt54",        "gpt-5.4-pro",              True),
    ("DeepSeek-V3.1",            "azure_ai",     "DeepSeek-V3.1",            False),
    ("DeepSeek-V4-Pro",          "azure_ai",     "DeepSeek-V4-Pro",          False),
    ("DeepSeek-V4-Flash",        "azure_ai",     "DeepSeek-V4-Flash",        False),
    ("DeepSeek-R1",              "azure_ai",     "DeepSeek-R1",              True),
    ("Llama-3.3-70B",            "azure_ai",     "Llama-3.3-70B-Instruct",   False),
    ("Mistral-Large-3",          "azure_ai",     "Mistral-Large-3",          False),
    ("grok-4-20-non-reasoning",  "azure_ai",     "grok-4-20-non-reasoning",  False),
    ("grok-4-1-fast-reasoning",  "azure_ai",     "grok-4-1-fast-reasoning",  True),
]

msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER_MSG}]

ai_client = OpenAI(base_url=ENDPOINT_AI, api_key=KEY, timeout=60)
oai_client = AzureOpenAI(api_version="2024-12-01-preview", azure_endpoint=ENDPOINT_OAI, api_key=KEY, timeout=60)

# SSL context for gpt-5.4-pro urllib calls
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def call_gpt54(deployment):
    url = f"{ENDPOINT_OAI}openai/responses?api-version=2025-04-01-preview"
    body = {"model": deployment, "input": [{"role": "user", "content": USER_MSG}], "instructions": SYSTEM, "max_output_tokens": 1000}
    req = Request(url, data=json.dumps(body).encode(), headers={"api-key": KEY, "Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=180, context=ssl_ctx) as resp:
        data = json.loads(resp.read().decode())
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    return c["text"]
    return str(data)

total = len(MODELS)
print(f"\nTest item: sf_06 (unique_monodefinite, expected=high)")
print(f"Sentence: {SENTENCE}")
print(f"Testing {total} models (Kimi removed, gpt-5.5/gpt-5.4-pro fixed)...\n")
print(f"{'#':<3} {'Model':<28} {'Rating':<8} {'Time':>6}  {'Status'}")
print("-" * 65)

for i, (name, mtype, deployment, reasoning) in enumerate(MODELS, 1):
    t0 = time.time()
    try:
        if mtype == "gpt54":
            raw = call_gpt54(deployment)
        elif mtype == "azure_openai":
            kwargs = {"model": deployment, "messages": msgs, "max_completion_tokens": 10}
            if not reasoning:
                kwargs["temperature"] = 0.7
            raw = oai_client.chat.completions.create(**kwargs).choices[0].message.content
        else:
            max_tok = 2000 if reasoning else 10
            kwargs = {"model": deployment, "messages": msgs, "max_tokens": max_tok}
            if not reasoning:
                kwargs["temperature"] = 0.7
            raw = ai_client.chat.completions.create(**kwargs).choices[0].message.content

        # Parse rating
        text = raw.strip()
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        digits = "".join(c for c in text if c.isdigit())
        rating = int(digits[:2]) if digits else None

        elapsed = time.time() - t0
        print(f"{i:<3} {name:<28} {str(rating):<8} {elapsed:>5.1f}s  OK")
        sys.stdout.flush()
    except Exception as e:
        elapsed = time.time() - t0
        err = str(e)[:80]
        print(f"{i:<3} {name:<28} {'---':<8} {elapsed:>5.1f}s  ERROR: {err}")
        sys.stdout.flush()

print(f"\nDone. {total}/{total} tested.")
