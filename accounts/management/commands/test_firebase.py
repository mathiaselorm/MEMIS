from django.core.management.base import BaseCommand
from firebase_admin import auth

class Command(BaseCommand):
    help = 'Tests Firebase SDK by attempting to verify a Firebase ID token'

    def handle(self, *args, **options):
        try:
            # Dummy token for example purposes. Replace with a real token for an actual test.
            id_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImNlMzcxNzMwZWY4NmViYTI5YTUyMTJkOWI5NmYzNjc1NTA0ZjYyYmMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYXNlbXBhLWJyYW5kLThjODNlIiwiYXVkIjoiYXNlbXBhLWJyYW5kLThjODNlIiwiYXV0aF90aW1lIjoxNzIyOTY3MTgyLCJ1c2VyX2lkIjoiNkZSZGFoTmpQUlNpTm14SnRiRFZMMlJ3TkJDMiIsInN1YiI6IjZGUmRhaE5qUFJTaU5teEp0YkRWTDJSd05CQzIiLCJpYXQiOjE3MjI5NjcxODIsImV4cCI6MTcyMjk3MDc4MiwiZW1haWwiOiJ2aXRlY2gxODBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInZpdGVjaDE4MEBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ.ANJ_jLTCDVfmjAwTr6gfycTcqylm03ZLJg1VdEPpDXvmFBwFyFv0Euu2KW46jA6AmyLUimse6wnkYo-jj_-LL8QGvQJUID5QsBjUrqc_ojWZAC2gwCdKW7nWWBdBin3YhVl_FKWjTy2knws4AN5Q2lzi4tOQPxRgMpZ6jFaVM81MKN-4Tn4BsRJXjajyrBryPBEalTlch2k8sRMrpEhlDt_R9iZRA33yBbdsSqJ0kIyZawbRkLOAGW6g2U9FYj2_NNLb5oZY_go2vvTyiF1oKJkDl8Heez9JOBinUVhgjwe9jOsWxOnuYgZPL_NJPoCes_foMUm6sy2HHxwdJ_bX1A"
            decoded_token = auth.verify_id_token(id_token)
            self.stdout.write(self.style.SUCCESS('Successfully verified Firebase ID token:'))
            self.stdout.write(str(decoded_token))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Failed to verify Firebase ID token:'))
            self.stdout.write(str(e))
