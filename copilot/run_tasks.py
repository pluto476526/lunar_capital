from copilot.tasks import fetch_forex_data

result = fetch_forex_data.delay()
print("Task sent:", result.id)

