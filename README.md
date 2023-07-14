# Restaurant-App-Fastapi-Backend
This is a dockerized fastapi based rest api for restaurants and bars that offer discounts in any given time of the day. 
Providers can notify consumers about their discounts and consumers can fetch the happy hours around them. 
This project is a base for restaurants that have happy hour system. The app works with geolocation capabilities in real time.

## To build the container

```
docker-compose -f docker-compose-dev.yml build 
```

## To run the container

```
docker-compose -f docker-compose-dev.yml up -d 
```
