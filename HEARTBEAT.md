# HEARTBEAT.md — Health Coach Agent

## Active Protocols

_(Updated automatically when fasting or exercise protocols are active)_

## Scheduled Crons

_(Sana will create and track scheduled check-ins here during active protocols)_

| Cron | Schedule | Job ID |
|------|----------|--------|
| (example) Morning Check-in | 08:00 daily | (auto) |
| (example) Evening Check-in | 21:00 daily | (auto) |

## Safety Monitoring

- Withings BP sync runs before every check-in (if configured)
- bp-analyze.py provides GREEN/YELLOW/RED classification
- RED thresholds: SBP <90 or >160, DBP <60 or >105
- Monitor for: dizziness, BP drops, palpitations, confusion

## Heartbeat Behaviour

- During fasting/refeeding periods: flag any user messages reporting symptoms
- Otherwise: HEARTBEAT_OK
