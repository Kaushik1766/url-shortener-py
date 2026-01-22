import boto3

from app.models.user import User
from app.repository.user_repo import UserRepository

def main():

    db = boto3.resource('dynamodb')
    repo = UserRepository(db)

    # repo.add_user(User(
    #     Username="Kaushik",
    #     Email="kaushik@a.com",
    #     PasswordHash="adsfasdf",
    #     ID="adfasf"
    # ))

    print(repo.get_user_by_email("kaushik@a.com"))
    print(repo.get_user_by_id("adfasf"))


if __name__ == "__main__":
    main()
