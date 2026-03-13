import csv
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import glob

class ScenariosView(APIView):
    def get(self, request):
        base_dir = getattr(settings, 'BASE_DIR', None)
        if base_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "simulation", "data")
        else:
            data_dir = "/home/kanishka/desis/project/grp-proj-desis/backend/simulation/data/"
             
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
        filenames = [os.path.basename(f) for f in csv_files]
        return Response({"scenarios": filenames}, status=status.HTTP_200_OK)

class MarketDataView(APIView):
    def get(self, request):
        scenario = request.query_params.get("scenario", "market_simulation_data.csv")
        
        # Prevent path traversal
        if "/" in scenario or "\\" in scenario or ".." in scenario:
            return Response({"error": "Invalid scenario name"}, status=status.HTTP_400_BAD_REQUEST)
            
        base_dir = getattr(settings, 'BASE_DIR', None)
        if base_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "simulation", "data")
            csv_path = os.path.join(data_dir, scenario)
        else:
            csv_path = f"/home/kanishka/desis/project/grp-proj-desis/backend/simulation/data/{scenario}"
             
        if not os.path.exists(csv_path):
             return Response({"error": "CSV data not found."}, status=status.HTTP_404_NOT_FOUND)

        data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        return Response({"data": data}, status=status.HTTP_200_OK)
