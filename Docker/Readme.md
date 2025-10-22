# Docker

Some docker informations.

# Proxy network
```
docker network create --ipv6 proxy
docker network create --ipv6 --subnet 2001:db8::/64 proxy
```
```
docker network create --ipv6 internal
docker network create --ipv6 --subnet 2001:db8:1::/64 internal
```