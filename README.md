# 📦 HappyRobot API – Load Search & Reporting

This is a mock logistics API built for a Forward Deployed Engineering take-home challenge. It allows:

- Load searching based on pickup location, destination, and equipment type.
- Receiving reports from AI agents (call results, negotiation outcomes).
- Viewing metrics and charts on a public dashboard.

---

## 🌐 Deployed Endpoints

> **Base URL (Fly.io)**  
> `https://happyrobot-take-home.fly.dev`  

---

## 🔑 Authentication

All endpoints (except `/dashboard`) require a valid `x-api-key` header. Contact @austenboodell@gmail.com for access. 

---

## 🚚 `/loads` — GET

### Description:
Return the best-matching load based on optional filters.

### Query Parameters:
- `origin`: pickup city/state (e.g., `Chicago, IL`)
- `destination`: delivery city/state
- `equipment_type` (optional): equiptment needed (`Dry Van`, `Flatbed`, `Reefer`)
- `pickup_datetime` (optional): date and time of pickup

### Example:

```bash
curl -G https://happyrobot-take-home.fly.dev/loads \
  -H "x-api-key: <enter_api_key>" \
  --data-urlencode "origin=Chicago, IL" \
  --data-urlencode "equipment_type=Dry Van"
```

---

## 📤 `/report` — POST

### Description:
Submit structured call outcome data.

### Body Format (`application/json`):

```json
{
  "origin": "Chicago, IL",
  "destination": "Dallas, TX",
  "equipment_type": "Dry Van",
  "loadboard_rate": 2200,
  "agreed_rate": 2100,
  "negotiation_result": "accepted",
  "call_duration_sec": 142
}
```

### Example:

```bash
curl -X POST https://happyrobot-take-home.fly.dev/report \
  -H "x-api-key: <enter_api_key>" \
  -H "Content-Type: application/json" \
  -d '{"origin":"Chicago, IL","destination":"Dallas, TX","equipment_type":"Dry Van","loadboard_rate":2200,"agreed_rate":2100,"negotiation_result":"accepted","call_duration_sec":142}'
```

---

## 📊 `/dashboard` — GET

### Description:
Displays a public HTML dashboard with:

- Total calls
- Deals closed and closing rate
- Average rate difference
- Average call length
- Bar charts:
  - Loadboard vs Agreed rate
  - Equipment frequency

> 📍 No authentication required

Open in browser:
```
https://happyrobot-take-home.fly.dev/dashboard
```

---

## 🔐 Security

- All endpoints (except `/dashboard`) require an API key (`x-api-key`).
- Deployed over HTTPS using Fly.io’s TLS support.
- API key authentication enforced using Flask decorators.

---

## 🚀 Deployment

This app is deployed on [Fly.io](https://fly.io).

### Run locally:

```bash
pip install flask
python app.py
```

### Deploy (after Docker & Fly CLI are installed):

```bash
fly launch
fly deploy
```

### Notes:
- Logs are saved in `call_reports.jsonl` for use in dashboard analytics.
- API will return a top match for any valid `/loads` query.

### Future Updates:
- Additional Metrics
- Data persistence between restarts
- Corrected call transfer to sales rep

---
