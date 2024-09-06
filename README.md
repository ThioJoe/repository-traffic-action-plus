# Repository Traffic GitHub Action

Github action that can be used to store repository traffic and clones past the default 2 week period. It pulls traffic, clones, referral sources, and referral paths data from the GitHub API v3 and stores it into CSV files, which can be committed to your repository or uploaded elsewhere.

# Features

- **Referral Website Data**: Now collects top referral sources (website domains) and referral paths in addition to repo views and clones.
- **Statistics Snapshot Archives**: Upon each run, in addition to the cumulative stats file, it creates a date-stamped zip archive containing all the generated files for that run.
- **Cumulative Data**: Maintains cumulative CSV files for long-term trend analysis.

# Usage

## Setting up permissions
You'll first need to create a fine grained personal access token (PAT) so the action can access the GitHub API. 

You can generate a PAT by going to 
Settings -> Developer Settings -> Personal Access Tokens -> Generate new token. 

If you just want to save the files externally (like to AWS S3), you will just need to grant a read-only "Administrative" permission under "Repositor Permissions".

To have the stats committed to the repo, you will need to grant read & write "contents" permission. For more in depth instructions, see the [GitHub documentation](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)

After you have generated the PAT, go to the "Settings" tab of the repository, click on New Secret, name the secret "TRAFFIC_ACTION_TOKEN" and copy the PAT into the box.

## Create a work flow

Create a `workflow.yml` file and place in your `.github/workflows` folder. You can reference the action from this workflow. The only required parameter is setting the PAT that was generated when setting up the permissions.
```yaml
    steps:
    # Calculates traffic, clones, and referral data and stores in CSV files
    - name: Repository Traffic 
      uses: ThioJoe/repository-traffic-action-plus@v0.2.2
      env:
        TRAFFIC_ACTION_TOKEN: ${{ secrets.TRAFFIC_ACTION_TOKEN }} 
```

This action stores the generated data in `${GITHUB_WORKPLACE}/traffic`. It creates the following files:
- Cumulative data: `views.csv`, `clones.csv`, `referral_sources.csv`, `referral_paths.csv`
- Snapshot: A zip file named `YYYY-MM-DD_snapshot.zip` containing the last 14 days of data

You can integrate other actions into the workflow to commit these files to your repository or upload them elsewhere. Below are two examples.

 ### Sample workflow that runs weekly and commits files to repository.

```yaml
on:
  schedule: 
    # runs once a week on sunday
    - cron: "55 23 * * 0"
    
jobs:
  # This workflow contains a single job called "traffic"
  traffic:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
    # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
    - uses: actions/checkout@v2
      with:
        ref: "traffic"
    
    # Calculates traffic, clones, and referral data and stores in CSV files
    - name: GitHub traffic 
      uses: ThioJoe/repository-traffic-action-plus@v0.2.2
      env:
        TRAFFIC_ACTION_TOKEN: ${{ secrets.TRAFFIC_ACTION_TOKEN }} 
     
    # Commits files to repository
    - name: Commit changes
      uses: EndBug/add-and-commit@v4
      with:
        author_name: Santiago Gonzalez
        message: "GitHub traffic"
        add: "./traffic/*"
        ref: "traffic"  # commits to branch "traffic" 
```
- Notes:
  - Ensure there is a branch in your repository with whatever ref value you use before running the action. If using the above values, you would create a branch "traffic".  
  - Ensure that the ref used in actions/checkoutv2 is the same in Endbug/add-and-commit@v4. 

### Sample workflow that runs weekly and uploads files to S3.
 
If you'd like to avoid committing the data to the repository, you can use another action to upload elsewhere. For example, you could download and upload files from S3 using other github actions.

```yaml
name: TrafficStatsPlusExampleWorkflow

on:
  schedule: 
    # runs once a week on sunday
    - cron: "55 23 * * 0"
  workflow_dispatch:
    
jobs:
  # This workflow contains a single job called "traffic"
  traffic:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
    # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
    - uses: actions/checkout@v2

    # Download from S3 - Leave this commented out if you only want the snapshots and don't care about the cumulative data files
    #- uses: prewk/s3-cp-action@master
    #  env:
    #    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    #    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    #    SOURCE: 's3://some-bucket/whatever-folder-name-within-bucket'
    #    DEST: 'traffic'
    
    # Calculates traffic and clones and stores in CSV file
	# This would be for the current repo running the action, but you can add the REPOSITORY_NAME variable to fetch another repo's stats (see next section for example).
    - name: Repository Traffic Plus
      uses: ThioJoe/repository-traffic-action-plus@v0.2.2
      env:
        TRAFFIC_ACTION_TOKEN: ${{ secrets.TRAFFIC_ACTION_TOKEN }}
     
    # Upload to S3
	# Be sure to set the proper AWS region for your bucket.
	# You can set "DEST_DIR" to whatever folder name you want within the bucket, but do not change the SOURCE_DIR, that is the temporary folder name within the github workspace
    - name: S3 Sync
      uses: jakejarvis/s3-sync-action@v0.5.1
      with:
        args: --follow-symlinks
      env:
        AWS_S3_BUCKET: ${{ secrets.AWS_S3_BUCKET }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_REGION: 'us-west-2'
        DEST_DIR: 'whatever-folder-name-within-bucket'
        SOURCE_DIR: 'traffic'
```
## Running from a different repository
If you'd like to get stats from a different repository than the one that you are running the github action, you can set the env variable "REPOSITORY_NAME". REPOSITORY_NAME should be formatted as "username/repository_name" or "organization_name/repository_name". The personal access token that you created in the first step should have access to the repository. For example:

```yaml
    steps:
    # Calculates traffic, clones, and referral data and stores in CSV files
    - name: Repository Traffic 
      uses: ThioJoe/repository-traffic-action-plus@v0.2.2
      env:
        TRAFFIC_ACTION_TOKEN: ${{ secrets.TRAFFIC_ACTION_TOKEN }}
        REPOSITORY_NAME: "YourUsername/Whatever-Repo-Name-To-Get-Stats"
```
