Movie-Recommendation-Platform-
Recommends movies to you

DATABASE

endpoint: movieplatformdatabase.ct6m2rqy8ajq.us-east-1.rds.amazonaws.com

username: admin password: Password1

TABLES

Movies

canonical_id PK
title
year
overview
poster_url
Genres

genre PK
External_ids

external_id PK
Ratings

canonical_id FK
site
rating
rating_id PK
MoviesGenres (Joining Table)

genre PK FK
canonical_id PK FK
MoviesExternal_ids

external_id PK FK
canonical P
