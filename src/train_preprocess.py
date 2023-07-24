from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np

class LrTaxiTransformer(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.features = ["PULocationID", "DOLocationID", "trip_distance", "passenger_count", "fare_amount", "total_amount"]
        self.target = 'duration'

    def fit(self, X, y=None):
        return self

    def transform(self, data):
        data = data.copy()
        data = self.calculate_and_filter_trip_duration_in_minutes(data)
        data = self.limit_passenger_count(data)
        
        y = data[self.target]
        X = data[self.features]
        return X, y

    def calculate_and_filter_trip_duration_in_minutes(self, data):
        data["duration"] = (
            data["lpep_dropoff_datetime"] - data["lpep_pickup_datetime"]
            ).dt.total_seconds() / 60
        data = data[(data["duration"] >= 1) & (data["duration"] <= 60)]
        return data
    
    def limit_passenger_count(self, data):
        data = data[(data['passenger_count'] > 0) & (data['passenger_count'] < 8)]
        return data