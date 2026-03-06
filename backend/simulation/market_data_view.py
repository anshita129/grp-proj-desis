import csv
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class MarketDataView(APIView):
    def get(self, request):
        # Path to the market_simulation_data.csv in the project root
        base_dir = getattr(settings, 'BASE_DIR', None)
        if base_dir:
            # Assuming market_simulation_data.csv is at the root level of the project
            # (same directory where manage.py typically lives or one level up)
            # For our current setup, it is in /home/kanishka/desis/project/grp-proj-desis/market_simulation_data.csv
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "market_simulation_data.csv")
        else:
             csv_path = "/home/kanishka/desis/project/grp-proj-desis/market_simulation_data.csv"
             
        if not os.path.exists(csv_path):
             return Response({"error": "CSV data not found."}, status=status.HTTP_404_NOT_FOUND)

        data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        return Response({"data": data}, status=status.HTTP_200_OK)
