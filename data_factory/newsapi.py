# @shared_task(bind=True, max_retries=3)
# def fetch_news_data(self):
#     """Fetch fresh financial news (raw, unsorted)"""
#     API_KEY = getattr(settings, "NEWS_API_KEY", None)
#     if not API_KEY:
#         logger.error("NEWS_API_KEY not set in settings.")
#         return {}

#     newsapi = NewsApiClient(API_KEY)

#     # restrict to last 24h
#     to_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
#     from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")

#     try:
#         news_data = newsapi.get_everything(
#             q="forex OR foreign exchange OR crypto OR cryptocurrency OR bitcoin OR ethereum OR stocks OR equities OR shares OR markets",
#             language="en",
#             sort_by="relevancy",
#             from_param=from_date,
#             to=to_date,
#             page_size=5
#         )

#         return news_data

#     except Exception as e:
#         logger.error(f"Error fetching news data: {e}")
#         try:
#             self.retry(exc=e, countdown=60)
#         except self.MaxRetriesExceededError:
#             logger.error("Max retries exceeded for news data fetch")
#         return []


