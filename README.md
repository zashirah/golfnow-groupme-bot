# golfnow-groupme-bot 

## Running the bot

## Prerequisites

Need to create the following in AWS:
   - ECR Repository
   - ECR Container
  
## Currently for development, you must load the parameters to AWS. Need to create a local version for people to manually inclue params

#### Setting up dev environment to scrape the leaderboard
1. Clone down repo
2. `cd` into `development`
3. run `docker build -t golfnow-groupme-bot:selenium-dev .`
4. run `docker run -p 8888:8888 -v $PWD:/app -it --rm golfnow-groupme-bot:selenium-dev`
5. navigate to `localhost:8888`
6. copy the token from your terminal and paste it in your browser 


#### Running web scraper app locally (TODO)
1. Clone down repo
2. `cd` into `development`
3. if you haven't built to dev container, run `docker build -t golfnow-groupme-bot:selenium-dev .`
4. if the dev container isn't running, run `docker run -p 8888:8888 -v $PWD:/app -it --rm golfnow-groupme-bot:selenium-dev`
5. update the GROUPME_BOT_NAME, REGION, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY variables in app.py
6. run `docker ps` to get the container id then run `docker exec -it <container id> bash`
7. run `python app.py`


## Deployment

#### Deploying to AWS as lambda container image
1. Clone down repo
2. `cd` into `src`
3. build image: `docker build -t golfnow-groupme-bot-lambda:0.0.1 .`
4. log into aws: `aws --profile golfnow-groupme-bot ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 213319972073.dkr.ecr.us-east-1.amazonaws.com`
5. tag image: `docker tag golfnow-groupme-bot-lambda:0.0.1 213319972073.dkr.ecr.us-east-1.amazonaws.com/golfnow-groupme-bot-lambda:0.0.1`
6. push image: `docker push 213319972073.dkr.ecr.us-east-1.amazonaws.com/golfnow-groupme-bot-lambda:0.0.1`

#### Load Encrypted SSM Params (manual, `aws cli`, ci/cd)
to do

#### Load cloudformation (manual, `aws cli`, ci/cd)
to do

