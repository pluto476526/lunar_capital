from data_factory.tasks import fetch_polygon_fx_data

result = fetch_polygon_fx_data.delay()
print("Task sent:", result.id)

