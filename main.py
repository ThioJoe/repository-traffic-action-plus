import os
import json
from repostats import RepoStats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import requests


def main():
    if "REPOSITORY_NAME" in os.environ:
        repo_name = os.environ["REPOSITORY_NAME"]
    else:
        repo_name = os.environ["GITHUB_REPOSITORY"]
    repo_stats = RepoStats(
        repo_name, os.environ["TRAFFIC_ACTION_TOKEN"])

    workplace_path = "{}/{}".format(os.environ["GITHUB_WORKSPACE"], "traffic")
    if not os.path.exists(workplace_path):
        os.makedirs(workplace_path)
    print("Workplace path: ", workplace_path)

    views_path = "{}/{}".format(workplace_path, "views.csv")
    clones_path = "{}/{}".format(workplace_path, "clones.csv")
    plots_path = "{}/{}".format(workplace_path, "plots.png")

    views_frame = repo_stats.get_views(views_path)
    clones_frame = repo_stats.get_clones(clones_path)

    if os.environ.get("UPLOAD_KEY"):
        upload(repo_name, views_frame, clones_frame, os.environ["UPLOAD_KEY"])
    else:
        views_frame.to_csv(views_path)
        clones_frame.to_csv(clones_path)
        create_plots(views_frame, clones_frame, plots_path)


def upload(repo_name, views_frame, clones_frame, api_key):
    data = {repo_name: json.loads(views_frame.join(
        clones_frame, how='outer').to_json(orient='index'))}
    print(requests.put("http://localhost:3000/api/upload", json=data))


def create_plots(views_frame, clones_frame, plots_path):
    fig, axes = plt.subplots(nrows=2, figsize=(12, 10))
    fig.tight_layout(h_pad=6)

    for i, (frame, title) in enumerate([(views_frame, 'Views'), (clones_frame, 'Clones')]):
        if not frame.empty:
            ax = frame.tail(30).plot(ax=axes[i])
            
            # Rotate and align the tick labels so they look better
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Add labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('Count')
            ax.set_title(f'Repository {title} - Last 30 Days')
            
            # Add legend
            ax.legend(loc='upper left')
            
            # Adjust layout to prevent cutoff
            plt.tight_layout()

    plt.savefig(plots_path, bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    main()
