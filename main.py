import os
import json
from repostats import RepoStats
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
import requests
from datetime import datetime

def main():
    if "REPOSITORY_NAME" in os.environ:
        repo_name = os.environ["REPOSITORY_NAME"]
    else:
        repo_name = os.environ["GITHUB_REPOSITORY"]
    
    workplace_path = os.path.join(os.environ["GITHUB_WORKSPACE"], "traffic")
    if not os.path.exists(workplace_path):
        os.makedirs(workplace_path)
    
    print("Workplace path: ", workplace_path)
    
    repo_stats = RepoStats(repo_name, os.environ["TRAFFIC_ACTION_TOKEN"], workplace_path)
    
    views_path = os.path.join(workplace_path, "views.csv")
    clones_path = os.path.join(workplace_path, "clones.csv")
    referral_sources_path = os.path.join(workplace_path, "referral_sources.csv")
    referral_paths_path = os.path.join(workplace_path, "referral_paths.csv")
    plots_path = os.path.join(workplace_path, "plots.png")
    
    views_snapshot, views_cumulative = repo_stats.get_views(views_path)
    clones_snapshot, clones_cumulative = repo_stats.get_clones(clones_path)
    referral_sources_snapshot, referral_sources_cumulative = repo_stats.get_top_referral_sources(referral_sources_path)
    referral_paths_snapshot, referral_paths_cumulative = repo_stats.get_top_referral_paths(referral_paths_path)
    
    if os.environ.get("UPLOAD_KEY"):
        upload(repo_name, views_cumulative, clones_cumulative, referral_sources_cumulative, referral_paths_cumulative, os.environ["UPLOAD_KEY"])
    else:
        views_cumulative.to_csv(views_path)
        clones_cumulative.to_csv(clones_path)
        referral_sources_cumulative.to_csv(referral_sources_path)
        referral_paths_cumulative.to_csv(referral_paths_path)
        create_plots(views_snapshot, clones_snapshot, plots_path)


def upload(repo_name, views_frame, clones_frame, referral_sources_frame, referral_paths_frame, api_key):
    data = {
        repo_name: {
            "traffic": json.loads(views_frame.join(clones_frame, how='outer').to_json(orient='index')),
            "referral_sources": json.loads(referral_sources_frame.to_json(orient='records')),
            "referral_paths": json.loads(referral_paths_frame.to_json(orient='records'))
        }
    }
    print(requests.put("http://localhost:3000/api/upload", json=data))


def create_plots(views_frame, clones_frame, plots_path):
    fig, axes = plt.subplots(nrows=2, figsize=(12, 10))
    fig.tight_layout(h_pad=6)

    for i, (frame, title) in enumerate([(views_frame, 'Views'), (clones_frame, 'Clones')]):
        if not frame.empty:
            # Sort the dataframe by date
            frame = frame.sort_index()
            
            # Plot only the last 14 days (GitHub's data range)
            last_14_days = frame.last('14D')
            ax = last_14_days.plot(ax=axes[i], marker='o')
            
            # Rotate and align the tick labels so they look better
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Add labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('Count')
            ax.set_title(f'Repository {title} - Last 14 Days')
            
            # Add legend
            ax.legend(loc='upper left')
            
            # Ensure y-axis starts at 0
            ax.set_ylim(bottom=0)
            
            # Adjust layout to prevent cutoff
            plt.tight_layout()

    plt.savefig(plots_path, bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    main()
