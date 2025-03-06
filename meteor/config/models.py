from pydantic import BaseModel


class Secrets(BaseModel):
    class Bot(BaseModel):
        token: str = ''

    bot: Bot = Bot()

    class Database(BaseModel):
        uri: str = ''

    database: Database = Database()


class Settings(BaseModel):
    class Bot(BaseModel):
        color: str = ''
        status: str = ''

    bot: Bot = Bot()

    class Users(BaseModel):
        class User(BaseModel):
            name: str
            id: int

        owners: list[User] = []
        moderators: list[User] = []

    users: Users = Users()
