# Handles communication with The Movie Database API 
# providing functions for searching movies

#STEP 1
#Import Libaries
#import flask for web app
from flask import Flask, jsonify, request

#used to create each endpoint
from flask_restful import Api, Resource

#import requests to make calls to TMDP API, easier to send HTTP Get, Post 
import requests

#access enviroment variables to read in secret credentials and interacting with operating system
import os 

#reads hidden .env file and loads key values into the enviroment 
from dotenv import load_dotenv

#looks for file .env and loasds the api keys into the process
load_dotenv()

#STEP 2
#read the three TMDB credentials from .env into the current process
#None will be returned is variable is not set 

TmdbAccessToken = os.getenv("TmdbAccessToken")

TmdbApiKey = os.getenv("TmdbApiKey")

TmdbUrl = os.getenv("TmdbUrl")

#STEP 3
#Create Flask and API setup

#create app instance
app = Flask(__name__)

#create the flask restful api class
api = Api(app)

#STEP 4
#TMDB request header 
def _tmdbHeader() -> dict:
    #used for every API request
    return {
        "Authorization": f"Bearer {TmdbAccessToken}",
        "accept": "application/json",
    }

#STEP 5
#A get request to the TMDB API
#creates a url to send a HTTP request and return json data
def _tmdbGet(path: str, params: dict = None):
    #join TMDB URL and path
    url = f"{TmdbUrl}{path}"
    try:
        #send get request to TMDB
        response = requests.get(
            url,
            headers = _tmdbHeader(),
            params = params,
            timeout=10,
        )

        #raise the HTTP request and check for error
        response.raise_for_status()

        #parse the response body as JSON and return it alongside HTTP status
        return response.json(), response.status_code

    # This is used when the TMDB does not respond within the timelimit 
    # We must return a error
    except requests.exceptions.Timeout:
        return (
            {
                "error": "We're sorry, The movie Database in currently unavaliable, please try again later"
            },
            503,
        )

    #when raise_for_statues is used, when a error occurs
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502

        #is the bearer token is missing, expired or wrong
        if status == 401:
            return (
                {
                    "error": "Authentication failed, contact support"
                },
                502,
            )

        #if the request movie ID dosent exists
        if  status == 404:
            return {"error": "Movie was not found in databse"}, 404

        #Incase of any other HTTP errors
        return (
            {
                "error": "We're sorry, The movie Database in currently unavaliable, please try again later"
            },
            502,
        )

    #when the network fails to connect to TMDB
    except requests.exceptions.ConnectionError:
        return (
            {
                "error": "Sorry, could not reach movie database, try again later"
            },
            503,
        )

    #for all other exceptions that havent been included
    except Exception:
        return (
            {
               "error": "Unexpected error, please try again shortly q" 
            },
            500,
        )

    #STEP 3
    #extract fields from TMDB database
def _extractMovieFields(movie: dict) -> dict:

    #extract poster URL
    poster_path = movie.get("poster_path")
    poster_url = (
        f"https://image.tmdb.org/t/p/w500{poster_path}"
        if poster_path
        else None
    )

    #extract release year
    release_date = movie.get("release_date", "")
    releaseYear = release_date[:4] if release_date else None

    #extract genre 
    genres = [g["name"] for g in movie.get("genres", [])]
    if not genres:
        genres = movie.get("genre_ids", [])

    #extract cast and directors
    credits = movie.get("credits", {})

    #Build list of top billed cast members
    cast = [
        {
            "name": member.get("name"),
            "character": member.get("character"),
            "profileUrl": (
                f"https://image.tmdb.org/t/p/w185{member['profile_path']}"
                if member.get("profile_path")
                else None
            )
        }
        #10 cast members
        for member in credits.get("cast", [])[:10]
    ]

    #extract directors from crew list
    directors = [
        crewMember.get("name")
        for crewMember in credits.get("crew", [])
        if crewMember.get("job") == "Director"
    ]

    #assemble the dictionary
    return {
        "tmdbID": movie.get("id"),
        "title": movie.get("title") or movie.get("original_title"),

        "releaseYear": releaseYear,
        "genres": genres,
        "plot": movie.get("overview"),
        "poster_url": poster_url,
        "rating": movie.get("vote_average"),
        "runtime": movie.get("runtime"),
        "cast": cast if cast else None,
        "directors": directors if directors else None,
    }
    

    #STEP 4
    #resourse classes
class healthCheck(Resource):
    #simple health check

    def get(self):
        return {"status": "ok", "service": "tmdbApi"}, 200

    #Movie search

class movieSearch(Resource):
    #Search TMDB for movies matching a text query 

    def get(self):
        query = request.args.get("query", "").strip()

        if not query:
            return {"error": "A search query is required"}, 400

        page = request.args.get("page", 1)

        data, status = _tmdbGet(
            "/search/movie",
            params = {
                "query": query,
                "page": page,
                "include_adult": False,
            },
        )

        #if TmdbGet encounters a error 
        if "error" in data:
            return data, status

        #transform results
        results = [_extractMovieFields(m) for m in data.get("results", [])]

        return {
            "page": data.get("page"),
            "totalResults": data.get("total_results"),
            "totalPages": data.get("total_pages"),
            "results": results,
        }, 200

        #STEP 5 
        #Movie Details

#retrieve movie details by the TMDB ID
class movieDetail(Resource):
    def get(self, tmdbID: int):
        data, status = _tmdbGet(
            f"/movie/{tmdbID}",
            params={"append_to_response": "credits"},
        )

        if "error" in data:
            return data, status

        return _extractMovieFields(data), 200

#STEP 6
#Movie recommendations
    
#Retrieve TMDB auto generated reccomendations for gven movies
class movieRecommendations(Resource):
    def get(self, tmdbID: int):
        page = request.args.get("page", 1)

        data, status = _tmdbGet(
            f"/movie/{tmdbID}/recommendations",
            params={"page": page},
        )

        if "error" in data:
            return data, status

        #transform recommended movies
        results = [_extractMovieFields(m) for m in data.get("results", [])]

        return {
            "page": data.get("page"),
            "totalResults": data.get("total_results"),
            "totalPages": data.get("total_pages"),
            "results": results,
        }, 200

#STEP 7
#Movie Cast

#Retrieve full cast and director information for a movie 
class MovieCast(Resource):
    def get(self, tmdbID: int):
        data, status = _tmdbGet(f"/movie/{tmdbID}/credits")

        if "error" in data:
            return data, status

        #build casts list
        cast = [
            {
                "name": member.get("name"),
                "character": member.get("character"),
                "order": member.get("order"),
                "profileUrl": (
                    f"https://image.tmdb.org/t/p/w185{member['profile_path']}"
                    if member.get("profile_path")
                    else None
                ),
            }
            for member in data.get("cast", [])
        ]

        #Build directors List
        directors = [
            {
                "name": crewMember.get("name"),
                "job": crewMember.get("job"),
                "profileUrl": (
                    f"https://image.tmdb.org/t/p/w185{crewMember['profile_path']}"
                    if crewMember.get("profile_path")
                    else None
                ),
            }
            for crewMember in data.get("crew", [])
            if crewMember.get("job") == "Director"
        ]

        #return TMDB with data
        return {
            "tmdbID": tmdbID,
            "cast": cast,
            "directors": directors,
        }, 200

#Register resources with API

api.add_resource(healthCheck, "/health")
api.add_resource(movieSearch, "/api/movies/search")
api.add_resource(movieDetail, "/api/movies/<int:tmdbID>")
api.add_resource(movieRecommendations, "/api/movies/<int:tmdbID>/recommendations")
api.add_resource(MovieCast, "/api/movies/<int:tmdbID>/cast")

#Entry Point
if __name__ == "__main__":
    app.run(debug=True, port=5000)
