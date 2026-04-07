# Ad Optimization Agent

This project builds a simple ad optimization agent that reallocates daily budget across Search, Social, and Display channels.

## Goal
Maximize conversions by shifting budget toward better-performing channels using simple rules and guardrails.

## Files
- `ad_optimization_agent.ipynb` or `ad_optimization_agent.py`: main code
- `mock_ad_data.csv`: 14-30 days of sample ad data
- `decision_log.csv`: reasons for daily budget changes
- `evaluation_comparison.csv`: comparison against equal-split baseline
- `design_doc.docx`: short design explanation
- `scaling_note.docx`: short note on cloud scaling
- `ad_optimization_agent_presentation.pptx`: presentation slides

## What the code does
- Reads CSV data
- Calculates CTR, CVR, and conversion efficiency
- Reallocates budget daily across channels
- Applies guardrails like max daily shift and minimum budget share
- Logs reasons for each decision
- Compares performance to a baseline

## Result
The agent improved expected conversions compared with an equal budget split baseline.
