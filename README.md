# mock-amazon
A mock amazon that can use google protocol to communicate and coorperate with a mock UPS to achieve purchase and deliver functionalities.

The whole system is dependent on a world simulator where 'world' can be generated to manage warehouses and trucks, and a pair of amazon and UPS need to connect to one world for the system to work.

repository for the world simulator: https://github.com/yunjingliu96/world_simulator_exec.git

## Getting Started

This project is also wrapped in docker, you can run by typing
```
sudo docker-compose build
```
```
sudo docker-compose up
```
in the same directory as the docker-compose.yml file


## Communication setup

The mock-amazon has 2 sockets set up for communication with the UPS and 1 socket for world. The hostname and port configuration are located in the AmazonDaemon.py file.






