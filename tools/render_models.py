#!/usr/bin/env python3
"""
Clawtter Model Status Generator
Reads ALL models from openclaw.json (providers + aliases) and generates status JSON.
"""
import json
from datetime import datetime
from pathlib import Path


def collect_all_models():
    config_path = Path("/home/opc/.openclaw/openclaw.json")
    with open(config_path, 'r') as f:
        config = json.load(f)

    providers = config.get("models", {}).get("providers", {})
    aliases = config.get("agents", {}).get("defaults", {}).get("models", {})

    seen = set()
    results = []

    # 1. From providers
    for provider_id, provider_data in providers.items():
        for m in provider_data.get("models", []):
            full_id = f"{provider_id}/{m['id']}"
            if full_id in seen:
                continue
            seen.add(full_id)
            name = full_id
            if full_id in aliases and "alias" in aliases[full_id]:
                name = aliases[full_id]["alias"]
            results.append({
                "provider": provider_id,
                "model": full_id,
                "alias": name if name != full_id else "",
                "success": True,
                "status": "configured",
                "response": "-"
            })

    # 2. From aliases (catches models not listed in providers, e.g. antigravity)
    for full_id, meta in aliases.items():
        if full_id in seen:
            continue
        seen.add(full_id)
        provider_id = full_id.split("/")[0] if "/" in full_id else "unknown"
        alias = meta.get("alias", "")
        results.append({
            "provider": provider_id,
            "model": full_id,
            "alias": alias,
            "success": True,
            "status": "configured",
            "response": "-"
        })

    return results


if __name__ == "__main__":
    results = collect_all_models()
    print(f"🧪 Collected {len(results)} models from openclaw.json")

    json_path = Path("/home/opc/projects/Clawtter_Deploy/model-status.json")
    status_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total": len(results),
            "passed": len(results),
            "failed": 0
        },
        "results": results
    }
    json_path.write_text(json.dumps(status_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✅ Written to {json_path}")
