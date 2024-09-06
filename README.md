# Repository Traffic GitHub Action (Plus)

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

If you just want to save the files externally (like to AWS S3), you will just need to grant a read-only "Administrative" permission under "Repository Permissions".

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

 ### Full Sample workflow that runs weekly and commits files to repository.

```yaml
name: TrafficStatsPlusExampleWorkflow

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

    # Download from S3 - Leave this commented out if you only want the snapshots and don't care about the cumulative/combined CSV files
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

# AWS S3 Policy Examples
Example of Amazon/AWS S3 IAM policies you can assign to a user and use with the action.
Note: I'm not an expert on this so it might be possible to pare down the permissions a bit more, but these should still be pretty good to limit the scope of the permissions.

## Write-Only Policy for Private Bucket(s)
This would allow writing files but not downloading them from a private bucket, like if you don't care about the main CSV file being updated with the cumulative data, and only care about the snapshot archives being generated during each run for archiving purposes.

*Note:* The `ListBucket` permission will still allow listing items in the bucket, but not downloading them. And even though the `DeleteObject` permission isn't given, PutObject still allows overwriting.

In this example the bucket is called `example-bucket-name-one`. (And optionally additional buckets such as `example-bucket-name-two`, or you could create separate users/policies for each bucket).

```JSON
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket",
                "s3:PutBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::example-bucket-name-one",
                "arn:aws:s3:::example-bucket-name-one/*",
		"arn:aws:s3:::example-bucket-name-two",
                "arn:aws:s3:::example-bucket-name-two/*"
            ]
        }
    ]
}
```

## Read-Write Policy for Private Bucket(s)

Allows access download files from the bucket, so it can also retrieve the cumulative stats files and update them, in addition to just saving snapshots.

Note: I haven't tried this one myself, but I think it should work, it's the same as above but I just added the `GetObject` permission.

```JSON
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
		"s3:GetObject",
                "s3:ListBucket",
                "s3:PutBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::example-bucket-name-one",
                "arn:aws:s3:::example-bucket-name-one/*",
		"arn:aws:s3:::example-bucket-name-two",
                "arn:aws:s3:::example-bucket-name-two/*"
            ]
        }
    ]
}
```

## How to Use the AWS Policies

### Creating a new "user" specifically to use for the workflow with limited permissions:

 1. In AWS go to "Identity and Access Management (IAM)", then on the left under "Access Management" click "Users", then on the right click the button that says "Create User".
 2. Give it a descriptive name like "my-github-action-user" then hit Next.
 3. On the permissions page, select "Attach Policies Directly". Then look for the button that says "Create Policy". It will open a new tab/window to specify permissions. 
 4. In this new window, next to where it says "Policy Editor", switch the blue toggle to "JSON" (instead of the default Visual). Delete everything in the text box and paste in one of the policies above. Then hit Next.
 5. On the following page give the policy a descriptive name like "Write-Only-GitHub-Traffic-Bucket-Policy" or whatever you want. Then hit "Create Policy".
 6. Back in the window for setting permissions for the new user, click the Refresh button which is next to that 'Create Policy' button you clicked before. Then under "Permission Policies", either search for your the name of the policy you created, or in the "Filter by Type" dropdown, select "Customer Managed" and it will list only ones you've created.
 7. Click the checkbox next to your policy then hit Next. And on the next page click 'Create User'.

#### Alternatively, if you already created a user but just need to add the policy permission:

1. Assuming you already created a new user specifically to use for the workflow but didn't give it any permissions, go to the user page (In IAM > Users > WhateverUserName).
2. Then in the section that says “Permission Policies”, you’d click the dropdown that says “Add Permissions” > “Create Inline Policy”.
3. Then on the page that shows up, there should be a toggle on the right between “Visual” and “JSON” editor, so just click JSON, then delete anything there and replace it with the policy below. Then just hit next and continue on to save it.

### Getting the access keys for the AWS User to use in the action:

1. Navigate to the relevant user (In IAM > Users > WhateverUserName)
2. In the main part of the page below the 'Summary' box, look for the "Security credentials" tab and click that. (The default selected tab is 'Permissions, so look near that if you can't find it)
3. Scroll down to the section called "Access Keys" and click the "Create access key" button.
4. Select a use case, but I don't think this is very important. I chose 'Application running outside AWS'.  They all seem to give one warning or another about recommended alternatives, but I'm not familiar with all that. Then hit Next.
5. On this page give it a description and click the "Create Access Key" button.
6. Then on the next page you can copy the Access key (to set as the `AWS_ACCESS_KEY_ID` github environment variable) and Secret access key (to set as the `AWS_SECRET_ACCESS_KEY` environment variable)
