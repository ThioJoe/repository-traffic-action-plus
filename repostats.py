import pandas as pd
import requests
from typing import Dict, Any

class RepoStats:
    def __init__(self, repo: str, token: str) -> None:
        print("Repository name: ", repo)
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repo}/traffic"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_views(self, views_path: str):
        views = self._make_request("views", {"per": "day"})
        view_counts = self._get_counts(views, "views")
        return self._create_dataframe(view_counts, "views", views_path)

    def get_clones(self, clones_path: str):
        clones = self._make_request("clones", {"per": "day"})
        clone_counts = self._get_counts(clones, "clones")
        return self._create_dataframe(clone_counts, "clones", clones_path)
    
    def get_top_referral_sources(self, referral_sources_path):
        sources = self._make_request("popular/referrers")
        return self._create_referral_dataframe(sources, "referral_sources", referral_sources_path)

    def get_top_referral_paths(self, referral_paths_path):
        paths = self._make_request("popular/paths")
        return self._create_referral_dataframe(paths, "referral_paths", referral_paths_path)
    
    def _create_referral_dataframe(self, data, metric_type, file_path):
        if metric_type == "referral_sources":
            columns = ["referrer", "count", "uniques"]
        else:  # referral_paths
            columns = ["path", "title", "count", "uniques"]

        dataframe = pd.DataFrame(data, columns=columns)
        
        try:
            print(f"Attempt to read existing metrics for: {metric_type} in {file_path}")
            old_data = pd.read_csv(file_path)
            # Combine old and new data, keeping the latest data for each referrer/path
            if metric_type == "referral_sources":
                combined = pd.concat([old_data, dataframe]).drop_duplicates(subset=["referrer"], keep="last")
            else:  # referral_paths
                combined = pd.concat([old_data, dataframe]).drop_duplicates(subset=["path"], keep="last")
            dataframe = combined.sort_values("count", ascending=False).reset_index(drop=True)
        except Exception as e:
            print('Exception type is: ', e.__class__.__name__)
            print(f"Starting new metrics record for: {metric_type} in {file_path}")

        dataframe.to_csv(file_path, index=False)
        return dataframe

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _get_counts(self, data, metric_type):
        total_column = f"total_{metric_type}"
        unique_column = f"unique_{metric_type}"
        counts = {}
        for item in data[metric_type]:
            date = pd.to_datetime(item["timestamp"], utc=True).date()
            if date not in counts:
                counts[date] = {total_column: 0, unique_column: 0}
            counts[date][total_column] += item["count"]
            counts[date][unique_column] += item["uniques"]
        
        # Create a complete date range for the last 14 days
        end_date = pd.Timestamp.now(tz='UTC').floor('D')
        start_date = end_date - pd.Timedelta(days=13)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Fill in missing dates with zero values
        for date in date_range:
            if date.date() not in counts:
                counts[date.date()] = {
                    total_column: 0,
                    unique_column: 0
                }
        
        return counts

    def _create_dataframe(self, data, metric_type, file_path):
        total_column = f"total_{metric_type}"
        unique_column = f"unique_{metric_type}"
        try:
            print(f"Attempt to read existing metrics for: {metric_type} in {file_path}")
            old_data = pd.read_csv(file_path, index_col="_date", parse_dates=["_date"]).to_dict(orient="index")
            updated_dict = self._merge_dict(old_data, data, metric_type)
            dataframe = pd.DataFrame.from_dict(
                data=updated_dict, orient="index", columns=[total_column, unique_column])
        except Exception as e:
            print('Exception type is: ', e.__class__.__name__)
            print(f"Starting new metrics record for: {metric_type} in {file_path}")
            dataframe = pd.DataFrame.from_dict(
                data=data, orient="index", columns=[total_column, unique_column])
        
        # Convert index to datetime, handling timezone-aware strings
        dataframe.index = pd.to_datetime(dataframe.index, utc=True)
        
        # Handle duplicate dates by summing the values
        dataframe = dataframe.groupby(dataframe.index).sum()
        
        # Create a complete date range
        date_range = pd.date_range(start=dataframe.index.min(), end=dataframe.index.max(), freq='D')
        
        # Reindex the dataframe with the complete date range, filling missing values with 0
        dataframe = dataframe.reindex(date_range, fill_value=0)
        
        # Convert to timezone-naive
        dataframe.index = dataframe.index.tz_convert(None)
        
        dataframe.index.name = "_date"
        return dataframe

    def _merge_dict(self, old_data, new_data, metric_type):
        
        total_column = "total_{}".format(metric_type)
        unique_column = "unique_{}".format(metric_type)
        
        print("Merging data for: ", metric_type)
        
        for key in new_data:
            if key not in old_data:
                old_data[key] = new_data[key]
            else:
                if new_data[key][total_column] > old_data[key][total_column] or new_data[key][unique_column] > old_data[key][unique_column]:
                    old_data[key] = new_data[key]
        return old_data
