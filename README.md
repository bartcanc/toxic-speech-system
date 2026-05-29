# Toxic Speech System

Toxic Speech System is developed by [Bartosz Rakowski](https://github.com/bartcanc) and [Marcel Radtke](https://github.com/xMarcel17) as a part of a master thesis project.

This part consists of three main components: 
- **Server** - used as a main form of communication between the user and the database and the AI container. Users can create accounts and manage them as well as the SafeSound devices they have paired with their account.
- **AI Container** - used to handle user queries to a pretrained AI model, which can detect instances of hate speech, cyberbullying, potential scams and grooming attempts by analyzing strings provided by users.
- **Database** - used to store user data i.e. email addresses, passwords, device id's, toxicity logs, etc.

## 1. Setup

For now, the only way to access this project is to clone the repository:
```
git clone https://github.com/bartcanc/toxic-speech-system
```

### .env files

In order for the project to function properly, you will have to create a **.env file** in project root directory (toxic-speech-system).\
Here is the desired structure of a .env file:

```
SECRET_KEY="secret_key"                             #   used for password hashing
DB_USER="username"                                  #   database credentials
DB_PASSWORD="password"
DB_NAME="toxic_system_db"

EMAIL_SENDER="youremail@gmail.com"                  #   both used for the SMTP server
EMAIL_PASSWORD="1234 5678 9011 1213"                #   16-character password for a Google Account

MODEL_PATH="/path/to/model"                         #   path where the model and tokenizers will reside 
OUTPUT_DIR="/path/to/training/results"              #   path where the training checkpoints will be saved (for analysis)

                                                    #   paths to datasets used to train the model
CB_CSV_PATH="/path/to/cyberbullying/dataset.csv"    #   |   cyberbullying
SPAM_CSV_PATH="/path/to/spam/dataset.csv"           #   |   spam/scam
TOXIC_CSV_PATH="/path/to/toxicity/dataset.csv"      #   |   toxicity
GROOMING_CSV_PATH="/path/to/grooming/dataset.csv"   #   |   grooming
```

### Datasets

The model is conditioned to be trained on specifically formatted data. Here is the structure of a raw dataset that should be used for training:

| sentence      | target |
| ----------- | -----------: |
| I like your drawing!      | 0       |
| F*CK YOU   | 1        |

### Model training
Before attempting to train the AI model, make sure you have all the necessary libraries installed. You can install them using this command:

```
pip install -r ./training_requirements.txt
```

To start training the AI model, use this command:

```
python ./ai_research/train_model.py
```

During the training setup process, the data is tweaked to reflect one of the 4 categories:
- 0 - OK, nothing wrong with the sentence,
- 1 - TOXIC,
- 2 - SCAM,
- 3-  GROOMING.

This is what a processed training dataset should look like:

| sentence                                  | target            |
| -----------                               |       -----------:|
| I like your drawing!                      | 0  (OK)           |
| F*CK YOU                                  | 1  (TOXIC)        |
| Can you give me your credit card number?  | 2  (SCAM)         |
| Hey baby, can you send me some pics? ;)   | 3  (GROOMING)     |

Here are the datasets used for this project specifically:
| Dataset                                       | Source                                                                            | Used for                                  |Licence                        |
| -----------                                   |       -----------                                                                 |-                                          |-                              |
| **Toxic Comment Classification**              | https://www.kaggle.com/competitions/jigsaw-toxic-comment-classification-challenge |Detection of toxicity in speech            |**CC0 1.0 Universal / CC BY-SA 3.0** |
| **Cyberbullying Classification**              | https://www.kaggle.com/datasets/andrewmvd/cyberbullying-classification            |Detection of cyberbullying instances       |**CC BY 4.0**               |
| **SMS Spam Collection Dataset**               | https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset                 |Detection of scam attempts                  |**CC0**   |
| **PAN12 Deception Detection**                 | https://pan.webis.de/clef12/pan12-web/sexual-predator-identification.html         |Detection of potential grooming attempts   |**Restricted / Research Only**        |

In the end, the trained model will be located in the earlier specified **MODEL_PATH** location.

### Docker
When all the steps above have been completed, you can finally start up the server. You have two options:

Using Docker Compose:
```
docker compose up -d --build
```

Using Docker:
```
#   Microservice network
docker network create toxic_net

#   PostgreSQL volume
docker volume create pgdata

#   AI image
docker build -t toxic_ai_image ./ai_research

#   Backend image
docker build -t toxic_backend_image ./backend_api
```

```
#   Database container
docker run -d \
  --name toxic_system_db \
  --network toxic_net \
  --network-alias db \
  --restart unless-stopped \
  --env-file ./.env \
  -e POSTGRES_USER=${DB_USER} \
  -e POSTGRES_PASSWORD=${DB_PASSWORD} \
  -e POSTGRES_DB=${DB_NAME} \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15
```

```
#   AI server
docker run -d \
  --name toxic_system_ai \
  --network toxic_net \
  --network-alias ai_research \
  --restart unless-stopped \
  --env-file ./.env \
  -e MODEL_PATH=/app/model \
  -p 8001:8001 \
  -v ${MODEL_PATH}:/app/model:ro \
  toxic_ai_image
```

```
#   Backend API
docker run -d \
  --name toxic_system_backend \
  --network toxic_net \
  --network-alias backend \
  --restart unless-stopped \
  --env-file ./.env \
  -e DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}" \
  -e ai_research_URL="http://ai_research:8001/analyze" \
  -p 8000:8000 \
  toxic_backend_image
```

The server will be available at http://localhost:8000, you can test all the endpoints at http://localhost:8000/docs.

## 2. ...........