import os

print("===================================")
print("VDK UPDATE START")
print("===================================")

scripts = [

    "ga4_campaigns.py",
    "ga4_categories.py",
    "ga4_channels.py",
    "ga4_checkout_funnel.py",
    "ga4_devices.py",
    "ga4_funnel.py",
    "ga4_geo.py",
    "ga4_landing_pages.py",
    "ga4_pages.py",
    "ga4_pagespeed.py",
    "ga4_products.py",
    "ga4_seo.py",
    "ga4_site_search.py",
    "ga4_to_sheet.py",
    "generate_alerts.py",
    "generate_insights.py",
    "generate_opportunities.py",
    "generate_trends.py"

]

for script in scripts:

    print(f"\nSTARTING: {script}")

    result = os.system(f"python3 {script}")

    print(f"FINISHED: {script}")
    print(f"EXIT CODE: {result}")

print("\n===================================")
print("VDK UPDATE COMPLETE")
print("===================================")
