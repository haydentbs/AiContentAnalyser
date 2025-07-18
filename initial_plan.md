# Content Scorecard – **Local Agentic Prototype**

> **Goal** – A self‑contained desktop/web app that scores a draft against configurable guidelines using an LLM‑powered agent system. No external hosting, no authentication, single user.

---

## 1 Scope & Assumptions

| Item        | Decision                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Deployment  | Runs locally via `python -m scorecard` or `streamlit run main.py`.                                                  |
| LLM Access  | Either local model (e.g., Ollama, LM Studio) **or** your OpenAI key passed as env var; switchable in `config.toml`. |
| Persistence | Plain files:<br>• `guidelines.yaml` for rules<br>• `reports/*.json` for results.                                    |
| Users       | Single local user; no auth/roles.                                                                                   |
| Network     | Offline‑friendly except for optional API calls.                                                                     |

---

## 2 High‑Level Architecture

```
+-----------------------------------------------------+
| Streamlit UI (or CLI)                               |
|  – Draft input (textarea / file upload)             |
|  – Trigger "Score"                                  |
+-------------▲---------------------------------------+
              │
              │ calls
              │
+-------------┴---------------------------------------+
|   Agent Orchestrator (LangChain / CrewAI)           |
|   1. Load guidelines.yaml                           |
|   2. For each metric:                               |
|        MetricEvaluatorAgent → LLM                   |
|   3. Aggregate scores (weighted mean)               |
|   4. Save report JSON + Markdown                    |
+-------------▲---------------------------------------+
              │
              │ optional file read
              │
+-------------┴---------------------------------------+
|   Local File System                                 |
+-----------------------------------------------------+
```

Everything runs **in‑process**; no Celery, no Redis.

---

## 3 Code Layout

```
scorecard/
├── main.py            # Streamlit entry‑point
├── agents/
│     ├── base.py      # Agent template helpers
│     └── scorer.py    # Coordinator + MetricEvaluator agents
├── prompts/
│     └── metric_prompt.jinja
├── guidelines.yaml    # Default 5 categories × 3‑5 metrics
├── reports/           # Auto‑generated JSON + .md files
├── config.toml        # Model provider, weights, UI opts
└── tests/
      ├── test_agents.py
      └── fixtures/
```

Run:

```bash
pip install -r requirements.txt
streamlit run scorecard/main.py
```

---

## 4 Tech Choices (Local‑Optimised)

| Layer           | Library                          | Why                            |
| --------------- | -------------------------------- | ------------------------------ |
| Agent framework | **LangChain 0.2+** or **CrewAI** | Built‑in tool & memory support |
| UI              | **Streamlit 1.35**               | Zero‑config local webapp       |
| Config          | **Pydantic‑Settings**            | Type‑safe `.toml` parsing      |
| Storage         | Native FS (`pathlib`)            | Simplicity                     |
| Charts          | **Plotly** radar chart           | Works inside Streamlit         |
| Testing         | **Pytest** + `pytest‑mock`       | Fast local runs                |

---

## 5 Guideline Format (`guidelines.yaml`)

```yaml
clarity:
  weight: 1.0
  metrics:
    concise:
      description: "Is the writing free of filler words?"
      weight: 0.3
    jargon:
      description: "Jargon defined or avoided?"
      weight: 0.4
    structure:
      description: "Logical flow with headings?"
      weight: 0.3
accuracy:
  weight: 1.2
  metrics:
    data_support: {description: "Claims backed by data?", weight: 0.6}
    fact_check:  {description: "No factual errors?",  weight: 0.4}
# …three more categories
```

Users edit this file to tweak rules; no database needed.

---

## 6 Agent Design Sketch

```python
class MetricEvaluator(Agent):
    tools = [LLM("${MODEL}")]
    prompt = get_template("metric_prompt.jinja")
    def run(self, draft, metric):
        resp = self.tools[0].chat(self.prompt.format(**metric, draft=draft))
        return parse_score(resp)

class Coordinator(Agent):
    def run(self, draft):
        rules = load_guidelines()
        results = []
        for cat in rules:
            for metric in cat.metrics:
                score, comment = MetricEvaluator().run(draft, metric)
                results.append(...)
        return aggregate(results)
```

A single process, no concurrency needed for small drafts; but you can `asyncio.gather` if desired.

---

## 7 Front‑End Flow (Streamlit)

1. TextArea for draft *or* file‑upload (`.md`, `.txt`).
2. Button **Score Draft** → calls `Coordinator.run`.
3. Show:

   * Overall score (gauge)
   * Radar chart by category
   * Expanders listing each metric: *score, comment*.
   * Download buttons: **JSON** / **Markdown report**.

---

## 8 Testing Strategy

| Level | Technique                                       | Notes |
| ----- | ----------------------------------------------- | ----- |
| Unit  | Mock LLM with deterministic fixture text.       |       |
| Agent | Golden JSON snapshots compared with `jsondiff`. |       |
| UI    | Streamlit’s `session_state` unit tests.         |       |

Run all with `pytest -q`.

---

## 9 Mock Drafts for Quick Try‑Out

The three sample drafts (Alpha Robotics, Indian EdTech, GreenCharge) are included under `tests/fixtures/`. Use **Score Example Draft** button in the UI to pre‑load them.

---

### Next Steps

1. `poetry new scorecard` and paste the skeleton.
2. Write `metric_prompt.jinja` – keep output structured (`Score: x\nComment: ...`).
3. Implement `parse_score`; verify with unit tests.
4. Build minimal Streamlit page; wire to Coordinator.
5. Iterate on guideline weights, prompt wording, and UI polish.

*Ask whenever you’re ready for concrete code snippets or further simplifications!*

