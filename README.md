# ConsoleChat
## Content in development -> errors may occur

With this program you can connect to your self-hosted server and communicate with the other clients that are connected.
As you host your server, you are responsible for the content and security.
This messanger is not recommended for sending confidential data, such as passwords, etc. over it.

## Functions

- Create a account and use your own username and password
- Communicate with your friends over your self-hosted server

## How to use

- Make sure python is installed
- You need to install docker and docker-compose on your system
- Run the docker deamon
- Once docker and docker-compose are installed, run the file docker-compose.yml in the Server folder with this command: ```` docker-compose up -d ````
  
-  ## Install packages
  - Linux/MacOS:   
    - Run the install-dependencies.sh file
  - Windows:
    - Run the install-dependencies.bat file
         
- You just need to run the server.py file
- Next, you can run the client.py file, but make sure you connect to the same IP and port that the socket is running on

## Planed Features

- A chat history
- Timeout for the user if he/she is afk for a long time
