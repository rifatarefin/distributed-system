# Distributed System
## A client-server system for spell checking
Client registers with a username | ![c0](GUI/c0.png)
-----|------
Server accepts if the username is not taken by other clients | ![](GUI/s1.png)
Client uploads a text file to the server for spell checking against a lexicon of commonly misspelled words. Client can also add words to the server's lexicon. Server periodically polls each clients for new words in the lexicon | ![](GUI/c1.png)

### Backup

Primary server connects to a backup server and pushes the lexicon periodically | ![](GUI/bs.png)
-----|------
If primary server crashes, clients connect to this backup server | ![](GUI/bs2.png)
Normal operation goes on at the backup server until primary rejoins | ![](GUI/c2.png)
If both primary and backup dies, error message is shown to client | ![](GUI/c3.png)
