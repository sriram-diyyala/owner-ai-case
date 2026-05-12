import pandas as pd

calls = pd.read_csv('data/call_transcripts.csv')
calls.columns = [c.lower() for c in calls.columns]

print("=" * 60)
print("SHORT CALLS — FULL TRANSCRIPTS")
print("=" * 60)
short = calls[calls['call_duration_min'] < 2].sort_values('call_duration_min')
for _, row in short.iterrows():
    print(f"\nCall: {row['call_id']} | Duration: {row['call_duration_min']} min | Outcome: {row['call_outcome']} | Rep: {row['rep_id']}")
    print(f"Cuisine: {row['cuisine_type']} | Type: {row['restaurant_type']}")
    print("-" * 40)
    print(row['transcript'])

print("=" * 60)
print("UNKNOWN CUISINE — STATS + SAMPLES")
print("=" * 60)
unknown = calls[calls['cuisine_type'] == 'unknown']
print(f"Total unknown cuisine calls: {len(unknown)}")
print(f"Outcome breakdown: {unknown['call_outcome'].value_counts().to_dict()}")
print(f"Avg duration: {unknown['call_duration_min'].mean():.2f} min")
print(f"Duration by outcome:")
print(unknown.groupby('call_outcome')['call_duration_min'].mean().round(2))

for _, row in unknown.head(5).iterrows():
    print(f"\nCall: {row['call_id']} | {row['call_duration_min']} min | {row['call_outcome']} | {row['rep_id']}")
    print(row['transcript'][:500])

print("=" * 60)
print("UNKNOWN CUISINE — DEMO BOOKED SAMPLES")
print("=" * 60)
for _, row in unknown[unknown['call_outcome'] == 'demo_booked'].head(3).iterrows():
    print(f"\nCall: {row['call_id']} | {row['call_duration_min']} min | {row['rep_id']}")
    print(row['transcript'][:600])