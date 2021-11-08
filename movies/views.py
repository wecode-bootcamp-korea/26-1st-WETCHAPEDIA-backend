import json, re

from django.conf  import settings
from django.http  import JsonResponse, request
from django.views import View
from django.db.models import Q, Avg

from .models      import *


class MovieDetailView(View):
    def get(self, request, movie_id):
        try:
            movie   = Movie.objects.get(id=movie_id)
            results = { 
                "movie_basic_info": 
                    {
                        "title"        : movie.title,
                        "release_date" : str(movie.released_at),
                        "genre"        : [genre.name for genre in movie.genres.all()],
                        "country"      : movie.country,
                        "running_time" : movie.running_time_in_minute,
                        "short_comment": movie.description,
                        "poster_url"   : movie.poster_image_url,
                        "grade"        : movie.grade.name,
                        "rate"         : [rate.rate for rate in Rating.objects.filter(movie=movie_id)]
                    }
                    ,    
                "staffs": 
                    [
                        { 
                            "name"              : staff.staff.name, 
                            "position"          : staff.position, 
                            "role"              : staff.role , 
                            "profile_image_url" : staff.staff.profile_image_url
                        }
                        for staff in movie.moviestaff_set.all()
                    ]
                    ,
                "comments": 
                    [
                        {
                            "user_name"  : comment.user.name,
                            "comment"    : comment.description,
                            "like_number": LikeComment.objects.filter(comment = comment).count()
                        } 
                        for comment in Comment.objects.filter(movie=movie_id)
                    ]
            }
            return JsonResponse({"movie" : results}, status= 200)

        except KeyError:
            return JsonResponse({"message" : "KEY_ERROR"}, status=400)

        except Movie.DoesNotExist:
            return JsonResponse({"message" : "영화 정보가 없습니다."}, status=404)

class MovieListView(View):
    def get(self, request):
        source = request.GET.get("source")
        staff = request.GET.get("staff")
        title = request.GET.get("title")
        rating = request.GET.get("rating")
        OFFSET = int(request.GET.get("offset", 0))
        LIMIT = int(request.GET.get("display", 15))

        q = Q()
        if source:
            q.add(Q(sources__name=source), q.AND)

        if staff:
            q.add(Q(staffs__name=staff), q.AND)

        if title:
            q.add(Q(title__icontains=title), q.AND)

        if rating:
            q = Q()

        movies = (
            Movie.objects.filter(q)
            .annotate(average_point=Avg("rating__rate"))
            .order_by("-average_point")[OFFSET : OFFSET + LIMIT]
        )

        result = {
            "movies": [
                {
                    "id": movie.id,
                    "title": movie.title,
                    "poster_image_url": movie.poster_image_url,
                    "released_at": movie.released_at,
                    "country": movie.country,
                    "ratings": round(movie.average_point, 1) if movie.average_point != None else 0,
                    "sources": [source.name for source in movie.sources.all()],
                }
                for movie in movies
            ],
        }

        return JsonResponse({"message": result}, status=200)