#!/usr/bin/env python3
import psycopg2
import schedule
import time

def run_maintenance():
    """Run database maintenance tasks"""
    conn = psycopg2.connect(dbname='financial_data', user='finance_user', 
                           password='your_secure_password', host='localhost')
    cursor = conn.cursor()
    
    # Vacuum and analyze for performance
    cursor.execute("VACUUM ANALYZE market_data;")
    cursor.execute("VACUUM ANALYZE trading_metrics;")
    
    # Check for chunk maintenance
    cursor.execute("SELECT * FROM timescaledb_information.job_stats;")
    stats = cursor.fetchall()
    print("Job stats:", stats)
    
    conn.commit()
    cursor.close()
    conn.close()

# Schedule daily maintenance
schedule.every().day.at("02:00").do(run_maintenance)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
