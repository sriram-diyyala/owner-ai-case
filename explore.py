import pandas as pd
import json
from collections import Counter

calls = pd.read_csv('call_transcripts.csv')
restaurants = pd.read_csv('restaurants.csv')

calls.columns = [c.lower() for c in calls.columns]
restaurants.columns = [c.lower() for c in restaurants.columns]

print("=" * 60)
print("CALL TRANSCRIPTS — BASIC STATS")
print("=" * 60)
print(f"Total calls: {len(calls)}")
print(f"\nOutcome distribution:")
print(calls['call_outcome'].value_counts())
print(f"\nCall duration stats (minutes):")
print(calls['call_duration_min'].describe())
print(f"\nCuisine type distribution:")
print(calls['cuisine_type'].value_counts())
print(f"\nRestaurant type distribution:")
print(calls['restaurant_type'].value_counts())
print(f"\nRep IDs:")
print(calls['rep_id'].value_counts())
print(f"\nRep tenure distribution:")
print(calls['rep_tenure'].value_counts())

print("\n" + "=" * 60)
print("DATA QUALITY FLAGS")
print("=" * 60)
short_calls = calls[calls['call_duration_min'] < 2]
print(f"Calls under 2 min (likely voicemails): {len(short_calls)}")
print(short_calls[['call_id','call_duration_min','call_outcome','rep_id']].to_string())

print(f"\nNull values per column:")
print(calls.isnull().sum())

print(f"\nSample transcript (first 300 chars) from a DEMO_BOOKED call:")
demo = calls[calls['call_outcome'].str.upper() == 'DEMO_BOOKED'].iloc[0]
print(f"Call ID: {demo['call_id']} | Duration: {demo['call_duration_min']} min")
print(demo['transcript'][:300])

print(f"\nSample transcript (first 300 chars) from a NOT_BOOKED call:")
not_booked = calls[calls['call_outcome'].str.upper() != 'DEMO_BOOKED'].iloc[0]
print(f"Call ID: {not_booked['call_id']} | Duration: {not_booked['call_duration_min']} min")
print(not_booked['transcript'][:300])

print("\n" + "=" * 60)
print("OUTCOME BY SEGMENT")
print("=" * 60)
print("\nOutcome by cuisine type:")
print(pd.crosstab(calls['cuisine_type'], calls['call_outcome']))
print("\nOutcome by restaurant type:")
print(pd.crosstab(calls['restaurant_type'], calls['call_outcome']))
print("\nOutcome by rep tenure:")
print(pd.crosstab(calls['rep_tenure'], calls['call_outcome']))

print("\n" + "=" * 60)
print("DURATION ANALYSIS")
print("=" * 60)
print("\nAvg duration by outcome:")
print(calls.groupby('call_outcome')['call_duration_min'].mean().round(2))
print("\nAvg duration by rep:")
print(calls.groupby('rep_id')['call_duration_min'].mean().round(2))

print("\n" + "=" * 60)
print("RESTAURANTS")
print("=" * 60)
print(f"Total restaurants: {len(restaurants)}")
print(f"\nBy cuisine:")
print(restaurants['cuisine_type'].value_counts())
print(f"\nBy business type:")
print(restaurants['business_type'].value_counts())
print(f"\nBy state (top 10):")
print(restaurants['state'].value_counts().head(10))
print(f"\nNull values:")
print(restaurants.isnull().sum())