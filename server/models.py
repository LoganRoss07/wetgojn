from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List, Any
from uuid import UUID, uuid4

"""
Define internal Schema for our applications external API
This will force a consistent data structure for how we represent movies inside
our system, regardless of the website providing the data
all provider data will be transformed
"""

class RatingBundle(BaseModel):
    """As all providers will represent ratings differently 
    Inside each movie, ratings field will be a dictionary with 
    the key (provider name, i.e. TMDB) and value (providers rating, RatingBundle)
    """
    #Numeric Rating
    rating: Optional[float] = None

    #Number of votes
    votes: Optional[int] = None

    #Critic score
    critic_score: Optional[int] = None

    #audience score
    audience_score: Optional[int] = None

    #will need expanded if we use different providers which require more fields

class Movie(BaseModel):
    """
    movie is CORE internal data model for our External API
    Every movie will follow this same structure, from any provider
    """

    #Generate unique identifier from our system that we will use to refer to them
    canonical_id: UUID = Field(default_factory=uuid4)

    #Metadata, title of movie (will take from highest priority provider)
    title:str
    
    #Release year (some API's will not be able to provide this so optional)
    year: Optional[int] = None

    #list of genres, will default to an empty list, stops None errors
    genres: List[str] = Field(default_factory=list)

    #synopsis of the films
    overview: Optional[str] = None

    #URL pointing for movie image, HttpUrl used to validate URL
    poster_url: Optional[HttpUrl] = None

    #Provider Mapping, external_ids stores the websites specific IDs
    #Lets us use the ID's later for, rechecking data, merging provider data and avoiding duplicates
    external_ids: Dict[str, str] = Field(default_factory=dict)

    #ratings stores website ratings, keep original rating format

    ratings:Dict[str, RatingBundle] = Field(default_factory=dict)

    #provider_raw, store raw data from providers, stop excess calling of providers

    provider_raw: Dict[str, Any] = Field(default_factory=dict)
