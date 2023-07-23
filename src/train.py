import os
import argparse
import pandas as pd
import mlflow
from mlflow.tracking.client import MlflowClient
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from train_preprocess import LrTaxiTransformer

# Allow for argument from CLI call
parser = argparse.ArgumentParser()
parser.add_argument(
    "--cml_run", default=False, action=argparse.BooleanOptionalAction, required=True
)
args = parser.parse_args()
cml_run = args.cml_run


# Set variables
color = "green"
year = 2021
month = 1
model_name = "green-taxi-trip-duration-linr"


GOOGLE_APPLICATION_CREDENTIALS = "./credentials.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS


MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(model_name)
client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)


df = pd.read_parquet(f"./data/{color}_tripdata_{year}-{month:02d}.parquet")
transformer = LrTaxiTransformer()
X, y = transformer.fit_transform(df)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.2)


with mlflow.start_run() as run:
    
    tags = {
        "model": "linear regression",
        "developer": "joshuadbeil",
        "dataset": f"{color}-taxi",
        "year": year,
        "month": month,
        "features": transformer.features,
        "target": transformer.target
    }
    mlflow.set_tags(tags)
    
    lr = LinearRegression()
    lr.fit(X_train, y_train)

    y_pred_train = lr.predict(X_train)
    rmse_train = mean_squared_error(y_train, y_pred_train, squared=False)
    mlflow.log_metric("rmse train", rmse_train)

    y_pred_test = lr.predict(X_test)
    rmse_test = mean_squared_error(y_test, y_pred_test, squared=False)
    mlflow.log_metric("rmse test", rmse_test)
    
    mlflow.sklearn.log_model(lr, "model")

    run_id = run.info.run_id
    model_uri = f"runs:/{run_id}/model"
    registered_model = mlflow.register_model(model_uri=model_uri, name=model_name)

    latest_version_info = registered_model.get_latest_versions()[0]
    model_version = latest_version_info.version

    new_stage = "Production"
    client.transition_model_version_stage(
        name=model_name,
        version=model_version,
        stage=new_stage,
        archive_existing_versions=True
    )

if cml_run:
    with open("metrics.txt", "w") as f:
        f.write(f"RMSE on the Train Set: {rmse_train}")
        f.write(f"RMSE on the Test Set: {rmse_test}")
