# pyrefly: ignore [missing-import]
import strawberry
from users.schema import Query as UsersQuery, Mutation as UsersMutation

@strawberry.type
class Query(UsersQuery):
    pass

@strawberry.type
class Mutation(UsersMutation):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
