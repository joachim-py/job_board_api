from rest_framework.throttling import UserRateThrottle

class DeleteThrottle(UserRateThrottle):
    rate = '100/day' 